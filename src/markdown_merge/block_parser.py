"""Semantic Markdown block parser."""

from __future__ import annotations

import re

from markdown_merge.markdown_blocks import MarkdownBlock, MarkdownBlockType
from markdown_merge.tokenizer import TokenCounter

_FENCE_PATTERN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
_HEADING_PATTERN = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]+")
_LIST_PATTERN = re.compile(r"^[ \t]{0,3}(?:[-+*]|\d+[.)])[ \t]+")
_BLOCKQUOTE_PATTERN = re.compile(r"^[ \t]{0,3}>")
_THEMATIC_BREAK_PATTERN = re.compile(
    r"^[ \t]{0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})[ \t]*$"
)
_TABLE_SEPARATOR_PATTERN = re.compile(
    r"^[ \t]*\|?[ \t]*:?-{3,}:?[ \t]*(?:\|[ \t]*:?-{3,}:?[ \t]*)+\|?[ \t]*$"
)


def _fence_marker(line: str) -> tuple[str, int] | None:
    """Return fenced-code marker character and length."""
    match = _FENCE_PATTERN.match(line)
    if match is None:
        return None

    marker = match.group(1)
    return marker[0], len(marker)


def _is_closing_fence(
    line: str,
    fence_character: str,
    minimum_length: int,
) -> bool:
    """Return whether a line closes the active fenced-code block."""
    stripped = line.lstrip(" \t")

    if not stripped.startswith(fence_character * minimum_length):
        return False

    marker_length = 0

    for character in stripped:
        if character != fence_character:
            break
        marker_length += 1

    if marker_length < minimum_length:
        return False

    return stripped[marker_length:].strip() == ""


def _classify_simple_line(line: str) -> MarkdownBlockType | None:
    """Classify a single-line Markdown block."""
    stripped = line.rstrip("\r\n")

    if _HEADING_PATTERN.match(stripped):
        return MarkdownBlockType.HEADING

    if _THEMATIC_BREAK_PATTERN.match(stripped):
        return MarkdownBlockType.THEMATIC_BREAK

    if _BLOCKQUOTE_PATTERN.match(stripped):
        return MarkdownBlockType.BLOCKQUOTE

    if _LIST_PATTERN.match(stripped):
        return MarkdownBlockType.LIST

    return None


def _is_table_start(lines: list[str], index: int) -> bool:
    """Return whether two consecutive lines start a Markdown table."""
    if index + 1 >= len(lines):
        return False

    header = lines[index].rstrip("\r\n")
    separator = lines[index + 1].rstrip("\r\n")

    return "|" in header and _TABLE_SEPARATOR_PATTERN.match(separator) is not None


def _build_block(
    block_type: MarkdownBlockType,
    content: str,
    start_offset: int,
    end_offset: int,
    token_counter: TokenCounter,
) -> MarkdownBlock:
    """Build one validated semantic Markdown block."""
    return MarkdownBlock(
        block_type=block_type,
        content=content,
        token_count=token_counter.count(content),
        start_offset=start_offset,
        end_offset=end_offset,
        splittable=block_type
        not in {
            MarkdownBlockType.FENCED_CODE,
            MarkdownBlockType.TABLE,
        },
    )


def parse_markdown_blocks(
    text: str,
    token_counter: TokenCounter,
) -> list[MarkdownBlock]:
    """Parse Markdown into ordered semantic blocks without losing source text."""
    if not text:
        return []

    lines = text.splitlines(keepends=True)
    blocks: list[MarkdownBlock] = []

    index = 0
    offset = 0

    while index < len(lines):
        line = lines[index]
        stripped = line.rstrip("\r\n")

        if stripped.strip() == "":
            start = offset
            content_parts: list[str] = []

            while index < len(lines) and lines[index].rstrip("\r\n").strip() == "":
                content_parts.append(lines[index])
                offset += len(lines[index])
                index += 1

            blocks.append(
                _build_block(
                    block_type=MarkdownBlockType.RAW,
                    content="".join(content_parts),
                    start_offset=start,
                    end_offset=offset,
                    token_counter=token_counter,
                )
            )
            continue

        fence = _fence_marker(stripped)

        if fence is not None:
            start = offset
            fence_character, fence_length = fence
            content_parts = [line]

            offset += len(line)
            index += 1

            while index < len(lines):
                current = lines[index]
                current_stripped = current.rstrip("\r\n")

                content_parts.append(current)
                offset += len(current)
                index += 1

                if _is_closing_fence(
                    current_stripped,
                    fence_character=fence_character,
                    minimum_length=fence_length,
                ):
                    break

            blocks.append(
                _build_block(
                    block_type=MarkdownBlockType.FENCED_CODE,
                    content="".join(content_parts),
                    start_offset=start,
                    end_offset=offset,
                    token_counter=token_counter,
                )
            )
            continue

        if _is_table_start(lines, index):
            start = offset
            content_parts = [lines[index], lines[index + 1]]

            offset += len(lines[index]) + len(lines[index + 1])
            index += 2

            while index < len(lines):
                current = lines[index]

                if current.rstrip("\r\n").strip() == "" or "|" not in current:
                    break

                content_parts.append(current)
                offset += len(current)
                index += 1

            blocks.append(
                _build_block(
                    block_type=MarkdownBlockType.TABLE,
                    content="".join(content_parts),
                    start_offset=start,
                    end_offset=offset,
                    token_counter=token_counter,
                )
            )
            continue

        simple_type = _classify_simple_line(line)

        if simple_type in {
            MarkdownBlockType.HEADING,
            MarkdownBlockType.THEMATIC_BREAK,
        }:
            start = offset
            offset += len(line)
            index += 1

            blocks.append(
                _build_block(
                    block_type=simple_type,
                    content=line,
                    start_offset=start,
                    end_offset=offset,
                    token_counter=token_counter,
                )
            )
            continue

        if simple_type in {
            MarkdownBlockType.LIST,
            MarkdownBlockType.BLOCKQUOTE,
        }:
            start = offset
            content_parts = []

            while index < len(lines):
                current = lines[index]

                if current.rstrip("\r\n").strip() == "":
                    break

                current_type = _classify_simple_line(current)

                if current_type is not simple_type and content_parts:
                    break

                content_parts.append(current)
                offset += len(current)
                index += 1

            blocks.append(
                _build_block(
                    block_type=simple_type,
                    content="".join(content_parts),
                    start_offset=start,
                    end_offset=offset,
                    token_counter=token_counter,
                )
            )
            continue

        start = offset
        content_parts = []

        while index < len(lines):
            current = lines[index]
            current_stripped = current.rstrip("\r\n")

            if current_stripped.strip() == "":
                break

            if content_parts:
                if _fence_marker(current_stripped) is not None:
                    break

                if _is_table_start(lines, index):
                    break

                if _classify_simple_line(current) is not None:
                    break

            content_parts.append(current)
            offset += len(current)
            index += 1

        blocks.append(
            _build_block(
                block_type=MarkdownBlockType.PARAGRAPH,
                content="".join(content_parts),
                start_offset=start,
                end_offset=offset,
                token_counter=token_counter,
            )
        )

    return blocks
