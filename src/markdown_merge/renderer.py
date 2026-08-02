"""Markdown rendering functions."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from markdown_merge.models import DocumentSegment
from markdown_merge.tokenizer import TokenCounter


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
    token_limit: int,
    encoding_name: str,
    token_counter: TokenCounter,
) -> str:
    """Render a complete merged output document."""
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    unique_sources = len({segment.source_path for segment in segments})

    header = (
        f"# OpenAI Documentation Merge — Part {part_number}\n\n"
        f"- Generated: `{generated_at}`\n"
        f"- Token encoding: `{encoding_name}`\n"
        f"- Maximum tokens per part: `{token_limit:,}`\n"
        f"- Source documents represented: `{unique_sources:,}`\n"
        f"- Source segments represented: `{len(segments):,}`\n\n"
    )

    toc = render_toc(segments)
    body = "".join(segment.rendered_content for segment in segments)

    document = f"{header}{toc}\n{body}".strip() + "\n"

    if token_counter.count(document) > token_limit:
        raise RuntimeError("Rendered document exceeded the configured token limit.")

    return document
