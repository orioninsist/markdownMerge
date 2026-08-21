"""Tests for semantic Markdown block models."""

import pytest

from markdown_merge.markdown_blocks import MarkdownBlock, MarkdownBlockType


def test_fenced_code_block_is_valid_when_not_splittable() -> None:
    block = MarkdownBlock(
        block_type=MarkdownBlockType.FENCED_CODE,
        content="```python\nprint('ok')\n```",
        token_count=10,
        start_offset=0,
        end_offset=27,
        splittable=False,
    )

    assert block.block_type is MarkdownBlockType.FENCED_CODE
    assert block.splittable is False


def test_fenced_code_block_rejects_splittable_state() -> None:
    with pytest.raises(ValueError, match="Fenced code blocks cannot be splittable"):
        MarkdownBlock(
            block_type=MarkdownBlockType.FENCED_CODE,
            content="```text\ncontent\n```",
            token_count=5,
            start_offset=0,
            end_offset=19,
            splittable=True,
        )


@pytest.mark.parametrize(
    ("token_count", "start_offset", "end_offset", "message"),
    [
        (-1, 0, 1, "token_count cannot be negative"),
        (1, -1, 1, "start_offset cannot be negative"),
        (1, 5, 4, "end_offset cannot be lower than start_offset"),
    ],
)
def test_block_rejects_invalid_boundaries(
    token_count: int,
    start_offset: int,
    end_offset: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        MarkdownBlock(
            block_type=MarkdownBlockType.PARAGRAPH,
            content="content",
            token_count=token_count,
            start_offset=start_offset,
            end_offset=end_offset,
            splittable=True,
        )
