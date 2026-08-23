"""Source document splitting utilities."""

from __future__ import annotations

from markdown_merge.models import DocumentSegment, SourceDocument
from markdown_merge.renderer import render_segment
from markdown_merge.tokenizer import TokenCounter


def split_source_document(
    document: SourceDocument,
    token_budget: int,
    token_counter: TokenCounter,
    minimum_split_search_tokens: int = 512,
) -> list[DocumentSegment]:
    """Split oversized source documents into token-safe segments."""

    del minimum_split_search_tokens

    full_rendered = render_segment(
        source_path=document.relative_path,
        segment_index=1,
        segment_count=1,
        content=document.content,
    )

    full_tokens = token_counter.count(full_rendered)

    if full_tokens <= token_budget:
        return [
            DocumentSegment(
                source_path=document.relative_path,
                segment_index=1,
                segment_count=1,
                content=document.content,
                rendered_content=full_rendered,
                token_count=full_tokens,
            )
        ]

    safe_budget = int(token_budget * 0.90)

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    lines = document.content.splitlines(keepends=True)

    for line in lines:
        line_tokens = token_counter.count(line + "\n")

        if current and current_tokens + line_tokens > safe_budget:
            chunks.append("".join(current))
            current = []
            current_tokens = 0

        current.append(line)
        current_tokens += line_tokens

    if current:
        chunks.append("".join(current))

    segments: list[DocumentSegment] = []

    total = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        rendered = render_segment(
            source_path=document.relative_path,
            segment_index=index,
            segment_count=total,
            content=chunk,
        )

        segments.append(
            DocumentSegment(
                source_path=document.relative_path,
                segment_index=index,
                segment_count=total,
                content=chunk,
                rendered_content=rendered,
                token_count=token_counter.count(rendered),
            )
        )

    return segments
