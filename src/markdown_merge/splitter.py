"""Markdown-aware source splitting."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from markdown_merge.models import DocumentSegment, SourceDocument
from markdown_merge.renderer import render_segment
from markdown_merge.tokenizer import TokenCounter

_FENCE_PATTERN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
_HEADING_PATTERN = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+")
_THEMATIC_BREAK_PATTERN = re.compile(
    r"^[ \t]{0,3}(?:"
    r"(?:\*[ \t]*){3,}|"
    r"(?:-[ \t]*){3,}|"
    r"(?:_[ \t]*){3,}"
    r")[ \t]*$"
)


@dataclass(frozen=True, slots=True)
class _Boundary:
    """A candidate Markdown split position."""

    position: int
    priority: int


def _fence_marker(line: str) -> tuple[str, int] | None:
    """Return the opening/closing fence marker and length for a line."""
    match = _FENCE_PATTERN.match(line)
    if match is None:
        return None

    marker = match.group(1)
    return marker[0], len(marker)


def _is_closing_fence(
    line: str,
    fence_character: str,
    minimum_length: int,
) -> bool:
    """Return whether a line closes the currently active fenced block."""
    stripped = line.lstrip(" \t")
    if not stripped.startswith(fence_character * minimum_length):
        return False

    marker_length = 0
    for character in stripped:
        if character != fence_character:
            break
        marker_length += 1

    if marker_length < minimum_length:
        return False

    return stripped[marker_length:].strip() == ""


def _markdown_boundaries(text: str) -> list[_Boundary]:
    """Collect useful split boundaries that are outside fenced code blocks."""
    boundaries: dict[int, int] = {}
    offset = 0
    in_fence = False
    fence_character = ""
    fence_length = 0
    previous_blank = False

    for line in text.splitlines(keepends=True):
        line_without_ending = line.rstrip("\r\n")
        line_start = offset
        line_end = offset + len(line)

        if in_fence:
            if _is_closing_fence(
                line_without_ending,
                fence_character=fence_character,
                minimum_length=fence_length,
            ):
                in_fence = False
                fence_character = ""
                fence_length = 0
                boundaries[line_end] = max(boundaries.get(line_end, 0), 90)

            offset = line_end
            previous_blank = line_without_ending.strip() == ""
            continue

        marker = _fence_marker(line_without_ending)
        if marker is not None:
            fence_character, fence_length = marker
            in_fence = True

            if line_start > 0:
                boundaries[line_start] = max(boundaries.get(line_start, 0), 95)

            offset = line_end
            previous_blank = False
            continue

        stripped = line_without_ending.strip()
        is_blank = stripped == ""

        if _HEADING_PATTERN.match(line_without_ending):
            if line_start > 0:
                boundaries[line_start] = max(boundaries.get(line_start, 0), 100)

        elif line_start > 0 and _THEMATIC_BREAK_PATTERN.match(line_without_ending):
            boundaries[line_start] = max(boundaries.get(line_start, 0), 98)

        if is_blank:
            boundaries[line_end] = max(boundaries.get(line_end, 0), 80)

        elif previous_blank and line_start > 0:
            boundaries[line_start] = max(boundaries.get(line_start, 0), 85)

        boundaries[line_end] = max(boundaries.get(line_end, 0), 20)

        offset = line_end
        previous_blank = is_blank

    return [
        _Boundary(position=position, priority=priority)
        for position, priority in sorted(boundaries.items())
        if 0 < position < len(text)
    ]


def _choose_safe_boundary(
    text: str,
    maximum_content_tokens: int,
    minimum_split_search_tokens: int,
    token_counter: TokenCounter,
) -> int:
    """Choose the best Markdown boundary near the maximum token capacity."""
    token_ids = token_counter.encode(text)

    if len(token_ids) <= maximum_content_tokens:
        return len(text)

    maximum_prefix = token_counter.decode(token_ids[:maximum_content_tokens])
    maximum_character = len(maximum_prefix)

    search_floor_tokens = max(
        1,
        maximum_content_tokens - minimum_split_search_tokens,
    )
    search_floor_prefix = token_counter.decode(token_ids[:search_floor_tokens])
    search_floor_character = len(search_floor_prefix)

    candidates = [
        boundary
        for boundary in _markdown_boundaries(maximum_prefix)
        if search_floor_character <= boundary.position <= maximum_character
    ]

    if candidates:
        best_priority = max(boundary.priority for boundary in candidates)
        same_priority = [boundary for boundary in candidates if boundary.priority == best_priority]
        return max(boundary.position for boundary in same_priority)

    return maximum_character


def _largest_prefix_within_limit(
    text: str,
    maximum_content_tokens: int,
    minimum_split_search_tokens: int,
    token_counter: TokenCounter,
) -> tuple[str, str]:
    """Split text into the largest safe prefix and remaining suffix."""
    token_ids = token_counter.encode(text)

    if len(token_ids) <= maximum_content_tokens:
        return text, ""

    character_boundary = _choose_safe_boundary(
        text=text,
        maximum_content_tokens=maximum_content_tokens,
        minimum_split_search_tokens=minimum_split_search_tokens,
        token_counter=token_counter,
    )
    candidate = text[:character_boundary].rstrip()

    if not candidate:
        candidate = token_counter.decode(token_ids[:maximum_content_tokens]).rstrip()

    while candidate and token_counter.count(candidate) > maximum_content_tokens:
        candidate_tokens = token_counter.encode(candidate)
        candidate = token_counter.decode(candidate_tokens[:maximum_content_tokens]).rstrip()

    if not candidate:
        raise RuntimeError("Unable to create a non-empty source segment.")

    remaining = text[len(candidate) :].lstrip()
    return candidate, remaining


def split_content_prefix(
    text: str,
    maximum_content_tokens: int,
    minimum_split_search_tokens: int,
    token_counter: TokenCounter,
) -> tuple[str, str]:
    """Split arbitrary Markdown content at the best safe boundary."""
    if maximum_content_tokens <= 0:
        raise ValueError("maximum_content_tokens must be positive.")

    if minimum_split_search_tokens < 0:
        raise ValueError("minimum_split_search_tokens cannot be negative.")

    return _largest_prefix_within_limit(
        text=text,
        maximum_content_tokens=maximum_content_tokens,
        minimum_split_search_tokens=minimum_split_search_tokens,
        token_counter=token_counter,
    )


def _maximum_content_tokens(
    source_path: Path,
    segment_index: int,
    assumed_segment_count: int,
    token_budget: int,
    token_counter: TokenCounter,
) -> int:
    """Calculate content capacity after source-wrapper overhead."""
    empty_wrapper = render_segment(
        source_path=source_path,
        segment_index=segment_index,
        segment_count=assumed_segment_count,
        content="",
    )
    wrapper_tokens = token_counter.count(empty_wrapper)
    maximum = token_budget - wrapper_tokens

    if maximum <= 0:
        raise ValueError("Token budget is too small for source metadata and separators.")

    return maximum


def split_source_document(
    document: SourceDocument,
    token_budget: int,
    token_counter: TokenCounter,
    minimum_split_search_tokens: int = 512,
) -> list[DocumentSegment]:
    """Split a source into segments that individually fit the budget."""
    if minimum_split_search_tokens < 0:
        raise ValueError("minimum_split_search_tokens cannot be negative.")

    whole_rendered = render_segment(
        source_path=document.relative_path,
        segment_index=1,
        segment_count=1,
        content=document.content,
    )
    whole_rendered_tokens = token_counter.count(whole_rendered)

    if whole_rendered_tokens <= token_budget:
        return [
            DocumentSegment(
                source_path=document.relative_path,
                segment_index=1,
                segment_count=1,
                content=document.content,
                rendered_content=whole_rendered,
                token_count=whole_rendered_tokens,
            )
        ]

    provisional_contents: list[str] = []
    remaining = document.content
    provisional_index = 1

    while remaining:
        maximum_content = _maximum_content_tokens(
            source_path=document.relative_path,
            segment_index=provisional_index,
            assumed_segment_count=9_999,
            token_budget=token_budget,
            token_counter=token_counter,
        )
        prefix, remaining = _largest_prefix_within_limit(
            text=remaining,
            maximum_content_tokens=maximum_content,
            minimum_split_search_tokens=minimum_split_search_tokens,
            token_counter=token_counter,
        )
        provisional_contents.append(prefix)
        provisional_index += 1

    segment_count = len(provisional_contents)
    segments: list[DocumentSegment] = []

    for index, content in enumerate(provisional_contents, start=1):
        rendered = render_segment(
            source_path=document.relative_path,
            segment_index=index,
            segment_count=segment_count,
            content=content,
        )
        rendered_tokens = token_counter.count(rendered)

        if rendered_tokens > token_budget:
            raise RuntimeError("A source segment exceeded its token budget after rendering.")

        segments.append(
            DocumentSegment(
                source_path=document.relative_path,
                segment_index=index,
                segment_count=segment_count,
                content=content,
                rendered_content=rendered,
                token_count=rendered_tokens,
            )
        )

    return segments
