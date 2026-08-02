"""Tests for token-safe source splitting."""

from pathlib import Path

from markdown_merge.models import SourceDocument
from markdown_merge.splitter import split_source_document
from markdown_merge.tokenizer import TokenCounter


def test_oversized_document_is_split_under_budget() -> None:
    counter = TokenCounter("o200k_base")
    content = "\n\n".join(
        f"## Section {index}\n\n" + ("documentation content " * 80) for index in range(40)
    )
    document = SourceDocument(
        absolute_path=Path("/tmp/source.md"),
        relative_path=Path("guide/source.md"),
        content=content,
        original_characters=len(content),
        cleaned_characters=len(content),
        content_tokens=counter.count(content),
    )

    segments = split_source_document(
        document=document,
        token_budget=2_000,
        token_counter=counter,
    )

    assert len(segments) > 1
    assert all(segment.token_count <= 2_000 for segment in segments)
    assert all(segment.segment_count == len(segments) for segment in segments)
