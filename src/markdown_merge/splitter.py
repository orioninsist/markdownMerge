"""Markdown-aware source splitting."""

from __future__ import annotations

import re
from pathlib import Path

from markdown_merge.models import DocumentSegment, SourceDocument
from markdown_merge.renderer import render_segment
from markdown_merge.tokenizer import TokenCounter

_SAFE_BOUNDARY_PATTERNS = (
    re.compile(r"\n(?=#{1,6}\s)", flags=re.MULTILINE),
    re.compile(r"\n(?=---\s*$)", flags=re.MULTILINE),
    re.compile(r"\n\n+", flags=re.MULTILINE),
    re.compile(r"\n", flags=re.MULTILINE),
)


def _find_safe_character_boundary(text: str, target_character: int) -> int:
    """Find the nearest useful Markdown boundary before a target position."""
    minimum_position = max(1, int(target_character * 0.70))

    for pattern in _SAFE_BOUNDARY_PATTERNS:
        candidates = [
            match.start()
            for match in pattern.finditer(
                text,
                minimum_position,
                min(len(text), target_character + 1),
            )
        ]
        if candidates:
            return candidates[-1]

    return target_character


def _largest_prefix_within_limit(
    text: str,
    maximum_content_tokens: int,
    token_counter: TokenCounter,
) -> tuple[str, str]:
    """Split text into the largest safe prefix and remaining suffix."""
    token_ids = token_counter.encode(text)

    if len(token_ids) <= maximum_content_tokens:
        return text, ""

    rough_prefix = token_counter.decode(token_ids[:maximum_content_tokens])
    character_boundary = _find_safe_character_boundary(
        rough_prefix,
        len(rough_prefix),
    )
    candidate = rough_prefix[:character_boundary].rstrip()

    if not candidate:
        candidate = rough_prefix.rstrip()

    while candidate and token_counter.count(candidate) > maximum_content_tokens:
        candidate_tokens = token_counter.encode(candidate)
        candidate = token_counter.decode(candidate_tokens[:maximum_content_tokens]).rstrip()

    if not candidate:
        raise RuntimeError("Unable to create a non-empty source segment.")

    remaining = text[len(candidate) :].lstrip()
    return candidate, remaining


def _maximum_content_tokens(
    source_path: Path,
    segment_index: int,
    assumed_segment_count: int,
    token_budget: int,
    token_counter: TokenCounter,
) -> int:
    """Calculate content capacity after source-wrapper overhead."""
    empty_wrapper = render_segment(
        source_path=source_path,
        segment_index=segment_index,
        segment_count=assumed_segment_count,
        content="",
    )
    wrapper_tokens = token_counter.count(empty_wrapper)
    maximum = token_budget - wrapper_tokens

    if maximum <= 0:
        raise ValueError("Token budget is too small for source metadata and separators.")

    return maximum


def split_source_document(
    document: SourceDocument,
    token_budget: int,
    token_counter: TokenCounter,
) -> list[DocumentSegment]:
    """Split a source into segments that individually fit the budget."""
    whole_rendered = render_segment(
        source_path=document.relative_path,
        segment_index=1,
        segment_count=1,
        content=document.content,
    )

    if token_counter.count(whole_rendered) <= token_budget:
        return [
            DocumentSegment(
                source_path=document.relative_path,
                segment_index=1,
                segment_count=1,
                content=document.content,
                rendered_content=whole_rendered,
                token_count=token_counter.count(whole_rendered),
            )
        ]

    provisional_contents: list[str] = []
    remaining = document.content
    provisional_index = 1

    while remaining:
        maximum_content = _maximum_content_tokens(
            source_path=document.relative_path,
            segment_index=provisional_index,
            assumed_segment_count=9_999,
            token_budget=token_budget,
            token_counter=token_counter,
        )
        prefix, remaining = _largest_prefix_within_limit(
            text=remaining,
            maximum_content_tokens=maximum_content,
            token_counter=token_counter,
        )
        provisional_contents.append(prefix)
        provisional_index += 1

    segment_count = len(provisional_contents)
    segments: list[DocumentSegment] = []

    for index, content in enumerate(provisional_contents, start=1):
        rendered = render_segment(
            source_path=document.relative_path,
            segment_index=index,
            segment_count=segment_count,
            content=content,
        )
        rendered_tokens = token_counter.count(rendered)

        if rendered_tokens > token_budget:
            raise RuntimeError("A source segment exceeded its token budget after rendering.")

        segments.append(
            DocumentSegment(
                source_path=document.relative_path,
                segment_index=index,
                segment_count=segment_count,
                content=content,
                rendered_content=rendered,
                token_count=rendered_tokens,
            )
        )

    return segments
