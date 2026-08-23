from __future__ import annotations

from dataclasses import dataclass

from markdown_merge.models import DocumentSegment


@dataclass(frozen=True)
class FilePack:
    segments: list[DocumentSegment]
    token_count: int


def pack_files(
    segments: list[DocumentSegment],
    token_limit: int,
) -> list[FilePack]:
    if token_limit <= 0:
        raise ValueError("token_limit must be positive")

    parts: list[FilePack] = []
    current: list[DocumentSegment] = []
    current_tokens = 0

    for segment in segments:
        if segment.token_count > token_limit:
            raise RuntimeError(f"Single markdown source exceeds token limit: {segment.source_path}")

        if current and current_tokens + segment.token_count > token_limit:
            parts.append(
                FilePack(
                    segments=current,
                    token_count=current_tokens,
                )
            )
            current = []
            current_tokens = 0

        current.append(segment)
        current_tokens += segment.token_count

    if current:
        parts.append(
            FilePack(
                segments=current,
                token_count=current_tokens,
            )
        )

    return parts
