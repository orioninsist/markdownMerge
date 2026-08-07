"""Pack source segments into token-limited output parts."""

from __future__ import annotations

from collections import Counter, deque
from pathlib import Path

from markdown_merge.models import DocumentSegment
from markdown_merge.renderer import render_document, render_segment
from markdown_merge.splitter import split_content_prefix
from markdown_merge.tokenizer import TokenCounter

_PROVISIONAL_SEGMENT_NUMBER = 999_999


def _document_fits(
    segments: list[DocumentSegment],
    part_number: int,
    token_limit: int,
    encoding_name: str,
    token_counter: TokenCounter,
) -> bool:
    """Return whether segments fit after complete final-document rendering."""
    try:
        render_document(
            part_number=part_number,
            segments=segments,
            token_limit=token_limit,
            encoding_name=encoding_name,
            token_counter=token_counter,
        )
    except RuntimeError:
        return False

    return True


def _build_segment(
    source_path: Path,
    segment_index: int,
    segment_count: int,
    content: str,
    token_counter: TokenCounter,
) -> DocumentSegment:
    """Build a segment and its rendered source wrapper."""
    rendered = render_segment(
        source_path=source_path,
        segment_index=segment_index,
        segment_count=segment_count,
        content=content,
    )

    return DocumentSegment(
        source_path=source_path,
        segment_index=segment_index,
        segment_count=segment_count,
        content=content,
        rendered_content=rendered,
        token_count=token_counter.count(rendered),
    )


def _provisional_segment(
    source_path: Path,
    content: str,
    token_counter: TokenCounter,
) -> DocumentSegment:
    """Build a conservatively sized temporary segment."""
    return _build_segment(
        source_path=source_path,
        segment_index=_PROVISIONAL_SEGMENT_NUMBER,
        segment_count=_PROVISIONAL_SEGMENT_NUMBER,
        content=content,
        token_counter=token_counter,
    )


def _normalize_segment_metadata(
    segments: list[DocumentSegment],
    token_counter: TokenCounter,
) -> list[DocumentSegment]:
    """Rebuild exact source segment indexes/counts after adaptive splitting."""
    source_counts = Counter(segment.source_path for segment in segments)
    source_indexes: Counter[Path] = Counter()
    normalized: list[DocumentSegment] = []

    for segment in segments:
        source_indexes[segment.source_path] += 1

        normalized.append(
            _build_segment(
                source_path=segment.source_path,
                segment_index=source_indexes[segment.source_path],
                segment_count=source_counts[segment.source_path],
                content=segment.content,
                token_counter=token_counter,
            )
        )

    return normalized


def _split_segment_for_residual_capacity(
    current: list[DocumentSegment],
    segment: DocumentSegment,
    part_number: int,
    token_limit: int,
    encoding_name: str,
    token_counter: TokenCounter,
    minimum_split_search_tokens: int,
) -> tuple[DocumentSegment, DocumentSegment] | None:
    """Split the next segment so its prefix fills useful residual capacity."""
    empty_segment = _provisional_segment(
        source_path=segment.source_path,
        content="",
        token_counter=token_counter,
    )

    try:
        empty_document = render_document(
            part_number=part_number,
            segments=[*current, empty_segment],
            token_limit=token_limit,
            encoding_name=encoding_name,
            token_counter=token_counter,
        )
    except RuntimeError:
        return None

    available_content_tokens = token_limit - token_counter.count(empty_document)

    if available_content_tokens < minimum_split_search_tokens:
        return None

    segment_content_tokens = token_counter.count(segment.content)

    if segment_content_tokens <= available_content_tokens:
        return None

    low = 1
    high = min(
        available_content_tokens,
        segment_content_tokens - 1,
    )
    best: tuple[str, str] | None = None

    while low <= high:
        candidate_budget = (low + high) // 2

        prefix, remainder = split_content_prefix(
            text=segment.content,
            maximum_content_tokens=candidate_budget,
            minimum_split_search_tokens=minimum_split_search_tokens,
            token_counter=token_counter,
        )

        if not prefix or not remainder:
            high = candidate_budget - 1
            continue

        prefix_tokens = token_counter.count(prefix)
        remainder_tokens = token_counter.count(remainder)

        if (
            prefix_tokens < minimum_split_search_tokens
            or remainder_tokens < minimum_split_search_tokens
        ):
            high = candidate_budget - 1
            continue

        prefix_segment = _provisional_segment(
            source_path=segment.source_path,
            content=prefix,
            token_counter=token_counter,
        )

        if _document_fits(
            segments=[*current, prefix_segment],
            part_number=part_number,
            token_limit=token_limit,
            encoding_name=encoding_name,
            token_counter=token_counter,
        ):
            best = (prefix, remainder)
            low = candidate_budget + 1
        else:
            high = candidate_budget - 1

    if best is None:
        return None

    prefix, remainder = best

    prefix_tokens = token_counter.count(prefix)
    remainder_tokens = token_counter.count(remainder)

    if (
        prefix_tokens < minimum_split_search_tokens
        or remainder_tokens < minimum_split_search_tokens
    ):
        return None

    return (
        _provisional_segment(
            source_path=segment.source_path,
            content=prefix,
            token_counter=token_counter,
        ),
        _provisional_segment(
            source_path=segment.source_path,
            content=remainder,
            token_counter=token_counter,
        ),
    )


def pack_segments(
    segments: list[DocumentSegment],
    token_limit: int,
    encoding_name: str,
    token_counter: TokenCounter,
) -> list[list[DocumentSegment]]:
    """Pack ordered source segments without exceeding the final token limit."""
    if not segments:
        return []

    parts: list[list[DocumentSegment]] = []
    current: list[DocumentSegment] = []

    for segment in segments:
        candidate = [*current, segment]
        candidate_part_number = len(parts) + 1

        if _document_fits(
            segments=candidate,
            part_number=candidate_part_number,
            token_limit=token_limit,
            encoding_name=encoding_name,
            token_counter=token_counter,
        ):
            current = candidate
            continue

        if not current:
            raise RuntimeError(
                f"Segment cannot fit in an empty output part: {segment.display_name}"
            )

        parts.append(current)
        current = [segment]

        if not _document_fits(
            segments=current,
            part_number=len(parts) + 1,
            token_limit=token_limit,
            encoding_name=encoding_name,
            token_counter=token_counter,
        ):
            raise RuntimeError(
                f"Segment cannot fit in an empty output part: {segment.display_name}"
            )

    if current:
        parts.append(current)

    return parts


def pack_segments_adaptively(
    segments: list[DocumentSegment],
    token_limit: int,
    encoding_name: str,
    token_counter: TokenCounter,
    minimum_split_search_tokens: int,
) -> list[list[DocumentSegment]]:
    """Pack segments while using useful residual capacity semantically."""
    if not segments:
        return []

    if minimum_split_search_tokens < 0:
        raise ValueError("minimum_split_search_tokens cannot be negative.")

    queue = deque(segments)
    provisional_parts: list[list[DocumentSegment]] = []
    current: list[DocumentSegment] = []

    while queue:
        segment = queue.popleft()
        part_number = len(provisional_parts) + 1
        candidate = [*current, segment]

        if _document_fits(
            segments=candidate,
            part_number=part_number,
            token_limit=token_limit,
            encoding_name=encoding_name,
            token_counter=token_counter,
        ):
            current = candidate
            continue

        if not current:
            if not _document_fits(
                segments=[segment],
                part_number=part_number,
                token_limit=token_limit,
                encoding_name=encoding_name,
                token_counter=token_counter,
            ):
                raise RuntimeError(
                    f"Segment cannot fit in an empty output part: {segment.display_name}"
                )

            current = [segment]
            continue

        adaptive_split = _split_segment_for_residual_capacity(
            current=current,
            segment=segment,
            part_number=part_number,
            token_limit=token_limit,
            encoding_name=encoding_name,
            token_counter=token_counter,
            minimum_split_search_tokens=minimum_split_search_tokens,
        )

        if adaptive_split is None:
            provisional_parts.append(current)
            current = []
            queue.appendleft(segment)
            continue

        prefix_segment, remainder_segment = adaptive_split
        current.append(prefix_segment)
        provisional_parts.append(current)
        current = []
        queue.appendleft(remainder_segment)

    if current:
        provisional_parts.append(current)

    flattened = [segment for part in provisional_parts for segment in part]

    normalized = _normalize_segment_metadata(
        flattened,
        token_counter=token_counter,
    )

    return pack_segments(
        segments=normalized,
        token_limit=token_limit,
        encoding_name=encoding_name,
        token_counter=token_counter,
    )
