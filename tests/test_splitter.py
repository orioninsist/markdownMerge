"""Tests for immutable file-level splitting."""

from pathlib import Path

import pytest

from markdown_merge.models import SourceDocument
from markdown_merge.splitter import split_source_document
from markdown_merge.tokenizer import TokenCounter


def _document(content: str) -> tuple[SourceDocument, TokenCounter]:
    counter = TokenCounter("o200k_base")

    return (
        SourceDocument(
            absolute_path=Path("/tmp/guide/source.md"),
            relative_path=Path("guide/source.md"),
            original_characters=len(content),
            cleaned_characters=len(content),
            content=content,
            content_tokens=counter.count(content),
        ),
        counter,
    )


def test_source_document_creates_single_segment() -> None:
    document, counter = _document("# Guide\n\nSmall content.")

    segments = split_source_document(
        document=document,
        token_budget=1000,
        token_counter=counter,
    )

    assert len(segments) == 1

    segment = segments[0]

    assert segment.segment_index == 1
    assert segment.segment_count == 1
    assert segment.content == document.content
    assert segment.source_path == document.relative_path


def test_source_document_preserves_full_content() -> None:
    content = "# Title\n\n" + ("content " * 100)

    document, counter = _document(content)

    segments = split_source_document(
        document=document,
        token_budget=1000,
        token_counter=counter,
    )

    assert segments[0].content == content


def test_source_document_rejects_file_larger_than_budget() -> None:
    content = "# Large\n\n" + ("token " * 10_000)

    document, counter = _document(content)

    with pytest.raises(
        RuntimeError,
        match="Source file exceeds token budget without splitting",
    ):
        split_source_document(
            document=document,
            token_budget=1000,
            token_counter=counter,
        )
