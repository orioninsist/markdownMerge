"""Tests for Markdown rendering."""

from pathlib import Path

from markdown_merge.models import DocumentSegment
from markdown_merge.renderer import render_document, render_segment
from markdown_merge.tokenizer import TokenCounter


def test_render_document_contains_toc_and_source() -> None:
    counter = TokenCounter("o200k_base")
    rendered_segment = render_segment(
        source_path=Path("guide/start.md"),
        segment_index=1,
        segment_count=1,
        content="# Start\n\nContent",
    )
    segment = DocumentSegment(
        source_path=Path("guide/start.md"),
        segment_index=1,
        segment_count=1,
        content="# Start\n\nContent",
        rendered_content=rendered_segment,
        token_count=counter.count(rendered_segment),
    )

    result = render_document(
        part_number=1,
        segments=[segment],
        token_limit=80_000,
        encoding_name="o200k_base",
        token_counter=counter,
    )

    assert "## Table of Contents" in result
    assert "`guide/start.md`" in result
    assert "## Source: `guide/start.md`" in result
