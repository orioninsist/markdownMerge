"""Markdown rendering functions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from markdown_merge.models import DocumentSegment
from markdown_merge.tokenizer import TokenCounter


def calculate_reserve_tokens(
    segments: list[DocumentSegment],
    token_counter: TokenCounter,
) -> int:
    """Calculate generated Markdown overhead tokens."""
    header = (
        "# Markdown Merge — Part 1\n\n"
        "- Generated: `2026-01-01T00:00:00+00:00`\n"
        "- Token encoding: `o200k_base`\n"
        "- Maximum tokens per part: `1,500,000`\n"
        f"- Source documents represented: `{len({segment.source_path for segment in segments})}`\n"
        f"- Source segments represented: `{len(segments)}`\n\n"
    )

    toc_lines = ["## Table of Contents", ""]

    for segment in segments:
        display_name = segment.display_name
        anchor = slugify_markdown_anchor(f"source-{display_name}")
        toc_lines.append(f"- [`{display_name}`](#{anchor})")

    toc = "\n".join(toc_lines) + "\n\n"

    separator = "".join(
        (
            "\n---\n\n"
            f"## Source: `{segment.display_name}`\n\n"
            f"<!-- source-path: {segment.source_path.as_posix()} -->\n"
            f"<!-- source-segment: {segment.segment_index}/{segment.segment_count} -->\n\n"
        )
        for segment in segments
    )

    return token_counter.count(header + toc + separator)


def slugify_markdown_anchor(value: str) -> str:
    """Create a GitHub-compatible approximate Markdown anchor."""
    anchor = value.strip().casefold()
    anchor = anchor.replace("\\", "-").replace("/", "-")
    anchor = "".join(
        character
        for character in anchor
        if character.isalnum() or character in {" ", "-", "_", "."}
    )
    anchor = anchor.replace(" ", "-")
    while "--" in anchor:
        anchor = anchor.replace("--", "-")
    return anchor.strip("-")


def source_heading(display_name: str) -> str:
    """Render a deterministic source section heading."""
    return f"## Source: `{display_name}`"


def render_segment(
    source_path: Path,
    segment_index: int,
    segment_count: int,
    content: str,
) -> str:
    """Render one source segment with clear separators and metadata."""
    if segment_count == 1:
        display_name = source_path.as_posix()
    else:
        display_name = f"{source_path.as_posix()} (segment {segment_index}/{segment_count})"

    return (
        "\n---\n\n"
        f"{source_heading(display_name)}\n\n"
        f"<!-- source-path: {source_path.as_posix()} -->\n"
        f"<!-- source-segment: {segment_index}/{segment_count} -->\n\n"
        f"{content.strip()}\n"
    )


def render_toc(segments: list[DocumentSegment]) -> str:
    """Render a source-focused table of contents."""
    lines = ["## Table of Contents", ""]

    for segment in segments:
        display_name = segment.display_name
        anchor = slugify_markdown_anchor(f"source-{display_name}")
        lines.append(f"- [`{display_name}`](#{anchor})")

    return "\n".join(lines)


def render_document(
    part_number: int,
    segments: list[DocumentSegment],
    token_limit: int | None,
    encoding_name: str,
    token_counter: TokenCounter,
) -> str:
    """Render a complete merged output document."""
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    unique_sources = len({segment.source_path for segment in segments})

    token_line = (
        f"- Maximum tokens per part: `{token_limit:,}`\n"
        if token_limit is not None
        else "- Maximum tokens per part: `unlimited`\n"
    )

    header = (
        f"# Markdown Merge — Part {part_number}\n\n"
        f"- Generated: `{generated_at}`\n"
        f"- Token encoding: `{encoding_name}`\n"
        f"{token_line}"
        f"- Source documents represented: `{unique_sources:,}`\n"
        f"- Source segments represented: `{len(segments):,}`\n\n"
    )

    toc = render_toc(segments)
    body = "".join(segment.rendered_content for segment in segments)

    document = f"{header}{toc}\n{body}".strip() + "\n"

    return document
