"""Tests for semantic Markdown block parsing."""

from markdown_merge.block_parser import parse_markdown_blocks
from markdown_merge.markdown_blocks import MarkdownBlockType
from markdown_merge.tokenizer import TokenCounter


def _parse(text: str):
    return parse_markdown_blocks(text, TokenCounter("o200k_base"))


def test_parser_preserves_complete_source_without_loss_or_duplication() -> None:
    source = (
        "# Title\n\n"
        "Paragraph one.\n"
        "Paragraph two.\n\n"
        "```python\n"
        "print('hello')\n"
        "```\n\n"
        "- first\n"
        "- second\n"
    )

    blocks = _parse(source)

    assert "".join(block.content for block in blocks) == source


def test_parser_preserves_offsets_exactly() -> None:
    source = "# Title\n\nParagraph.\n"

    blocks = _parse(source)

    for block in blocks:
        assert source[block.start_offset : block.end_offset] == block.content


def test_parser_keeps_fenced_code_as_one_unsplittable_block() -> None:
    source = (
        "Before\n\n```python\ndef example():\n    return 42\n\n# Not a heading here\n```\n\nAfter\n"
    )

    blocks = _parse(source)

    fenced = [block for block in blocks if block.block_type is MarkdownBlockType.FENCED_CODE]

    assert len(fenced) == 1
    assert fenced[0].splittable is False
    assert "# Not a heading here" in fenced[0].content
    assert fenced[0].content.startswith("```python")
    assert fenced[0].content.rstrip().endswith("```")


def test_parser_supports_tilde_fenced_code() -> None:
    source = "~~~text\ncontent\n~~~\n"

    blocks = _parse(source)

    assert len(blocks) == 1
    assert blocks[0].block_type is MarkdownBlockType.FENCED_CODE
    assert blocks[0].content == source


def test_parser_detects_heading_and_paragraph() -> None:
    source = "# Heading\n\nParagraph content.\n"

    blocks = _parse(source)

    types = [block.block_type for block in blocks]

    assert types == [
        MarkdownBlockType.HEADING,
        MarkdownBlockType.RAW,
        MarkdownBlockType.PARAGRAPH,
    ]


def test_parser_detects_complete_table_as_unsplittable() -> None:
    source = "| Name | Value |\n| --- | --- |\n| one | 1 |\n| two | 2 |\n"

    blocks = _parse(source)

    assert len(blocks) == 1
    assert blocks[0].block_type is MarkdownBlockType.TABLE
    assert blocks[0].splittable is False
    assert blocks[0].content == source


def test_parser_groups_consecutive_list_items() -> None:
    source = "- one\n- two\n- three\n"

    blocks = _parse(source)

    assert len(blocks) == 1
    assert blocks[0].block_type is MarkdownBlockType.LIST
    assert blocks[0].content == source


def test_parser_groups_consecutive_blockquotes() -> None:
    source = "> first\n> second\n"

    blocks = _parse(source)

    assert len(blocks) == 1
    assert blocks[0].block_type is MarkdownBlockType.BLOCKQUOTE
    assert blocks[0].content == source


def test_parser_detects_thematic_break() -> None:
    blocks = _parse("---\n")

    assert len(blocks) == 1
    assert blocks[0].block_type is MarkdownBlockType.THEMATIC_BREAK


def test_empty_source_produces_no_blocks() -> None:
    assert _parse("") == []
