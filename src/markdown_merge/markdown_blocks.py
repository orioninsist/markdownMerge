"""Semantic Markdown block domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MarkdownBlockType(StrEnum):
    """Supported semantic Markdown block types."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    FENCED_CODE = "fenced_code"
    LIST = "list"
    TABLE = "table"
    BLOCKQUOTE = "blockquote"
    THEMATIC_BREAK = "thematic_break"
    RAW = "raw"


@dataclass(frozen=True, slots=True)
class MarkdownBlock:
    """One semantic Markdown block with source boundaries."""

    block_type: MarkdownBlockType
    content: str
    token_count: int
    start_offset: int
    end_offset: int
    splittable: bool

    def __post_init__(self) -> None:
        """Validate block invariants."""
        if self.token_count < 0:
            raise ValueError("token_count cannot be negative.")

        if self.start_offset < 0:
            raise ValueError("start_offset cannot be negative.")

        if self.end_offset < self.start_offset:
            raise ValueError("end_offset cannot be lower than start_offset.")

        if self.block_type is MarkdownBlockType.FENCED_CODE and self.splittable:
            raise ValueError("Fenced code blocks cannot be splittable.")
