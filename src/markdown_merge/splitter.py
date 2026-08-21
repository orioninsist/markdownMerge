"""Source-level segmentation without modifying Markdown content."""

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
    """
    Keep each source document atomic.

    Files are never split internally.
    Token limits are handled by the packer between files.
    """
    del minimum_split_search_tokens

    rendered = render_segment(
        source_path=document.relative_path,
        segment_index=1,
        segment_count=1,
        content=document.content,
    )

    token_count = token_counter.count(rendered)

    if token_count > token_budget:
        raise RuntimeError(
            f"Source file exceeds token budget without splitting: {document.relative_path}"
        )

    return [
        DocumentSegment(
            source_path=document.relative_path,
            segment_index=1,
            segment_count=1,
            content=document.content,
            rendered_content=rendered,
            token_count=token_count,
        )
    ]
