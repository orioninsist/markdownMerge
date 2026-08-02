"""Pack source segments into token-limited output parts."""

from __future__ import annotations

from markdown_merge.models import DocumentSegment
from markdown_merge.renderer import render_document
from markdown_merge.tokenizer import TokenCounter


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

        try:
            render_document(
                part_number=candidate_part_number,
                segments=candidate,
                token_limit=token_limit,
                encoding_name=encoding_name,
                token_counter=token_counter,
            )
        except RuntimeError:
            if not current:
                raise RuntimeError(
                    f"Segment cannot fit in an empty output part: {segment.display_name}"
                ) from None

            parts.append(current)
            current = [segment]

            render_document(
                part_number=len(parts) + 1,
                segments=current,
                token_limit=token_limit,
                encoding_name=encoding_name,
                token_counter=token_counter,
            )
        else:
            current = candidate

    if current:
        parts.append(current)

    return parts
