"""Pack source segments into token-limited output parts."""

from __future__ import annotations

from collections.abc import Callable

from markdown_merge.models import DocumentSegment, ProgressUpdate
from markdown_merge.renderer import calculate_reserve_tokens
from markdown_merge.tokenizer import TokenCounter

ProgressCallback = Callable[[ProgressUpdate], None]


def _noop_progress(update: ProgressUpdate) -> None:
    """Default progress callback."""
    del update


def pack_segments(
    segments: list[DocumentSegment],
    token_limit: int,
    encoding_name: str,
    token_counter: TokenCounter,
    progress_callback: ProgressCallback = _noop_progress,
) -> list[list[DocumentSegment]]:
    """Pack complete source segments without splitting them."""

    if not segments:
        return []

    parts: list[list[DocumentSegment]] = []
    current: list[DocumentSegment] = []
    current_tokens = 0

    total_segments = len(segments)

    for index, segment in enumerate(segments, start=1):
        progress_callback(
            ProgressUpdate(
                stage="Packing token-limited outputs",
                completed=index,
                total=total_segments,
                detail="Adding complete source files",
                current_source=segment.display_name,
                current_part=len(parts) + 1,
                current_tokens=current_tokens,
                token_limit=token_limit,
            )
        )

        candidate = [*current, segment]
        candidate_tokens = current_tokens + segment.token_count

        reserve_tokens = calculate_reserve_tokens(
            segments=candidate,
            token_counter=token_counter,
        )

        if candidate_tokens + reserve_tokens <= token_limit:
            current = candidate
            current_tokens = candidate_tokens
            continue

        if not current:
            raise RuntimeError(f"Single source segment exceeds token limit: {segment.display_name}")

        parts.append(current)
        current = [segment]
        current_tokens = segment.token_count

        reserve_tokens = calculate_reserve_tokens(
            segments=current,
            token_counter=token_counter,
        )

        if current_tokens + reserve_tokens > token_limit:
            raise RuntimeError(f"Single source segment exceeds token limit: {segment.display_name}")

    if current:
        parts.append(current)

    return parts
