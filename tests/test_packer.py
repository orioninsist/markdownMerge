"""Tests for ordered whole-segment packing."""

from pathlib import Path

import pytest

from markdown_merge.models import DocumentSegment
from markdown_merge.packer import pack_segments
from markdown_merge.renderer import render_document, render_segment
from markdown_merge.tokenizer import TokenCounter


def _segment(
    counter: TokenCounter,
    source_path: str,
    index: int,
    count: int,
    content: str,
) -> DocumentSegment:
    path = Path(source_path)
    rendered = render_segment(
        source_path=path,
        segment_index=index,
        segment_count=count,
        content=content,
    )

    return DocumentSegment(
        source_path=path,
        segment_index=index,
        segment_count=count,
        content=content,
        rendered_content=rendered,
        token_count=counter.count(rendered),
    )


def _rendered_tokens(
    counter: TokenCounter,
    segments: list[DocumentSegment],
    *,
    part_number: int,
    token_limit: int,
) -> int:
    rendered = render_document(
        part_number=part_number,
        segments=segments,
        token_limit=token_limit,
        encoding_name="o200k_base",
        token_counter=counter,
    )
    return counter.count(rendered)


def test_empty_segment_list_produces_no_parts() -> None:
    counter = TokenCounter("o200k_base")

    assert (
        pack_segments(
            segments=[],
            token_limit=4_000,
            encoding_name="o200k_base",
            token_counter=counter,
        )
        == []
    )


def test_complete_segments_that_fit_remain_in_same_part() -> None:
    counter = TokenCounter("o200k_base")

    segments = [
        _segment(
            counter,
            "001.md",
            1,
            1,
            "# One\n\n" + ("alpha content " * 300),
        ),
        _segment(
            counter,
            "002.md",
            1,
            1,
            "# Two\n\n" + ("beta content " * 300),
        ),
        _segment(
            counter,
            "003.md",
            1,
            1,
            "# Three\n\n" + ("gamma content " * 300),
        ),
    ]

    token_limit = 100_000

    parts = pack_segments(
        segments=segments,
        token_limit=token_limit,
        encoding_name="o200k_base",
        token_counter=counter,
    )

    assert len(parts) == 1
    assert parts[0] == segments


def test_next_complete_segment_moves_entirely_to_next_part_when_it_does_not_fit() -> None:
    counter = TokenCounter("o200k_base")

    first = _segment(
        counter,
        "001.md",
        1,
        1,
        "# One\n\n" + ("alpha content " * 1_000),
    )
    second = _segment(
        counter,
        "002.md",
        1,
        1,
        "# Two\n\n" + ("beta content " * 1_000),
    )
    third = _segment(
        counter,
        "003.md",
        1,
        1,
        "# Three\n\n" + ("gamma content " * 1_000),
    )

    generous_limit = 1_000_000

    two_segment_tokens = _rendered_tokens(
        counter,
        [first, second],
        part_number=1,
        token_limit=generous_limit,
    )

    three_segment_tokens = _rendered_tokens(
        counter,
        [first, second, third],
        part_number=1,
        token_limit=generous_limit,
    )

    assert three_segment_tokens > two_segment_tokens

    token_limit = three_segment_tokens - 1

    parts = pack_segments(
        segments=[first, second, third],
        token_limit=token_limit,
        encoding_name="o200k_base",
        token_counter=counter,
    )

    assert len(parts) == 2
    assert parts[0] == [first, second]
    assert parts[1] == [third]

    assert parts[1][0].source_path == Path("003.md")
    assert parts[1][0].content == third.content


def test_packing_preserves_original_source_order() -> None:
    counter = TokenCounter("o200k_base")

    segments = [
        _segment(
            counter,
            f"{index:03d}.md",
            1,
            1,
            f"# File {index}\n\n" + (f"content {index} " * 700),
        )
        for index in range(1, 8)
    ]

    token_limit = 4_000

    parts = pack_segments(
        segments=segments,
        token_limit=token_limit,
        encoding_name="o200k_base",
        token_counter=counter,
    )

    flattened = [segment for part in parts for segment in part]

    assert flattened == segments
    assert [segment.source_path for segment in flattened] == [
        segment.source_path for segment in segments
    ]


def test_packing_never_splits_or_modifies_segment_content() -> None:
    counter = TokenCounter("o200k_base")

    contents = {
        "001.md": "# One\n\n" + ("alpha text " * 800),
        "002.md": "# Two\n\n" + ("beta text " * 800),
        "003.md": "# Three\n\n" + ("gamma text " * 800),
        "004.md": "# Four\n\n" + ("delta text " * 800),
    }

    segments = [
        _segment(
            counter,
            source_path,
            1,
            1,
            content,
        )
        for source_path, content in contents.items()
    ]

    parts = pack_segments(
        segments=segments,
        token_limit=4_000,
        encoding_name="o200k_base",
        token_counter=counter,
    )

    flattened = [segment for part in parts for segment in part]

    assert len(flattened) == len(segments)

    for original, packed in zip(segments, flattened, strict=True):
        assert packed is original
        assert packed.source_path == original.source_path
        assert packed.content == original.content
        assert packed.segment_index == original.segment_index
        assert packed.segment_count == original.segment_count


def test_every_final_rendered_part_respects_token_limit() -> None:
    counter = TokenCounter("o200k_base")

    segments = [
        _segment(
            counter,
            f"{index:03d}.md",
            1,
            1,
            f"# File {index}\n\n" + (f"documentation {index} " * 700),
        )
        for index in range(1, 10)
    ]

    token_limit = 4_000

    parts = pack_segments(
        segments=segments,
        token_limit=token_limit,
        encoding_name="o200k_base",
        token_counter=counter,
    )

    assert parts

    for part_number, part in enumerate(parts, start=1):
        rendered = render_document(
            part_number=part_number,
            segments=part,
            token_limit=token_limit,
            encoding_name="o200k_base",
            token_counter=counter,
        )

        assert counter.count(rendered) <= token_limit


def test_single_segment_that_cannot_fit_empty_part_raises() -> None:
    counter = TokenCounter("o200k_base")

    segment = _segment(
        counter,
        "oversized.md",
        1,
        1,
        "# Oversized\n\n" + ("very large content " * 2_000),
    )

    with pytest.raises(
        RuntimeError,
        match="Single source segment exceeds token limit",
    ):
        pack_segments(
            segments=[segment],
            token_limit=1,
            encoding_name="o200k_base",
            token_counter=counter,
        )
