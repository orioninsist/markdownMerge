"""Tests for token-safe Markdown source splitting."""

from pathlib import Path

import pytest

from markdown_merge.models import SourceDocument
from markdown_merge.splitter import split_source_document
from markdown_merge.tokenizer import TokenCounter


def _document(content: str) -> tuple[SourceDocument, TokenCounter]:
    counter = TokenCounter("o200k_base")
    document = SourceDocument(
        absolute_path=Path("/tmp/source.md"),
        relative_path=Path("guide/source.md"),
        content=content,
        original_characters=len(content),
        cleaned_characters=len(content),
        content_tokens=counter.count(content),
    )
    return document, counter


def test_oversized_document_is_split_under_budget() -> None:
    content = "\n\n".join(
        f"## Section {index}\n\n" + ("documentation content " * 80) for index in range(40)
    )
    document, counter = _document(content)

    segments = split_source_document(
        document=document,
        token_budget=2_000,
        token_counter=counter,
    )

    assert len(segments) > 1
    assert all(segment.token_count <= 2_000 for segment in segments)
    assert all(segment.segment_count == len(segments) for segment in segments)


def test_split_prefers_heading_boundary_near_capacity() -> None:
    first_section = "# First\n\n" + ("alpha documentation text " * 350)
    second_section = "## Second\n\n" + ("beta documentation text " * 350)
    content = f"{first_section}\n\n{second_section}"
    document, counter = _document(content)

    first_section_tokens = counter.count(first_section)
    token_budget = first_section_tokens + 120

    segments = split_source_document(
        document=document,
        token_budget=token_budget,
        token_counter=counter,
        minimum_split_search_tokens=256,
    )

    assert len(segments) >= 2
    assert segments[0].content.startswith("# First")
    assert not segments[0].content.endswith("## Second")
    assert segments[1].content.startswith("## Second")
    assert all(segment.token_count <= token_budget for segment in segments)


def test_split_does_not_choose_boundary_inside_fenced_code_block() -> None:
    before = "# Before\n\n" + ("intro text " * 100)
    code_lines = "\n".join(f"print('line {index}')" for index in range(400))
    fenced = f"```python\n{code_lines}\n```"
    after = "## After\n\n" + ("closing text " * 100)
    content = f"{before}\n\n{fenced}\n\n{after}"
    document, counter = _document(content)

    token_budget = max(
        1_200,
        counter.count(before) + counter.count(fenced) // 2,
    )

    segments = split_source_document(
        document=document,
        token_budget=token_budget,
        token_counter=counter,
        minimum_split_search_tokens=512,
    )

    assert len(segments) > 1
    assert all(segment.token_count <= token_budget for segment in segments)

    for segment in segments[:-1]:
        fence_count = segment.content.count("```") + segment.content.count("~~~")
        assert fence_count % 2 == 0 or not segment.content.rstrip().endswith(("```", "~~~"))


def test_plain_text_falls_back_to_exact_token_safe_split() -> None:
    content = "documentation " * 5_000
    document, counter = _document(content)

    segments = split_source_document(
        document=document,
        token_budget=1_200,
        token_counter=counter,
        minimum_split_search_tokens=128,
    )

    assert len(segments) > 1
    assert all(segment.content for segment in segments)
    assert all(segment.token_count <= 1_200 for segment in segments)


def test_document_at_or_below_budget_is_not_split() -> None:
    content = "# Small\n\n" + ("content " * 100)
    document, counter = _document(content)

    segments = split_source_document(
        document=document,
        token_budget=2_000,
        token_counter=counter,
    )

    assert len(segments) == 1
    assert segments[0].content == content
    assert segments[0].segment_index == 1
    assert segments[0].segment_count == 1


def test_negative_split_search_tokens_is_rejected() -> None:
    content = "# Source\n\n" + ("content " * 1_000)
    document, counter = _document(content)

    with pytest.raises(
        ValueError,
        match="minimum_split_search_tokens cannot be negative",
    ):
        split_source_document(
            document=document,
            token_budget=1_000,
            token_counter=counter,
            minimum_split_search_tokens=-1,
        )
