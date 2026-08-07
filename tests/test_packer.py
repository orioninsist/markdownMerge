"""Tests for exact and adaptive segment packing."""

from pathlib import Path

from markdown_merge.models import DocumentSegment
from markdown_merge.packer import (
    pack_segments,
    pack_segments_adaptively,
)
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

    assert (
        pack_segments_adaptively(
            segments=[],
            token_limit=4_000,
            encoding_name="o200k_base",
            token_counter=counter,
            minimum_split_search_tokens=128,
        )
        == []
    )


def test_adaptive_packing_uses_residual_capacity() -> None:
    counter = TokenCounter("o200k_base")

    segments = [
        _segment(
            counter,
            "first.md",
            1,
            1,
            "# First\n\n" + ("first tail content " * 850),
        ),
        _segment(
            counter,
            "second.md",
            1,
            2,
            "## Second A\n\n" + ("second content alpha " * 1_000),
        ),
        _segment(
            counter,
            "second.md",
            2,
            2,
            "## Second B\n\n" + ("second content beta " * 1_000),
        ),
    ]

    token_limit = 4_000

    ordinary = pack_segments(
        segments=segments,
        token_limit=token_limit,
        encoding_name="o200k_base",
        token_counter=counter,
    )

    adaptive = pack_segments_adaptively(
        segments=segments,
        token_limit=token_limit,
        encoding_name="o200k_base",
        token_counter=counter,
        minimum_split_search_tokens=128,
    )

    assert len(adaptive) <= len(ordinary)

    ordinary_first_tokens = counter.count(
        render_document(
            part_number=1,
            segments=ordinary[0],
            token_limit=token_limit,
            encoding_name="o200k_base",
            token_counter=counter,
        )
    )

    adaptive_first_tokens = counter.count(
        render_document(
            part_number=1,
            segments=adaptive[0],
            token_limit=token_limit,
            encoding_name="o200k_base",
            token_counter=counter,
        )
    )

    assert adaptive_first_tokens >= ordinary_first_tokens
    assert all(
        counter.count(
            render_document(
                part_number=index,
                segments=part,
                token_limit=token_limit,
                encoding_name="o200k_base",
                token_counter=counter,
            )
        )
        <= token_limit
        for index, part in enumerate(adaptive, start=1)
    )


def test_adaptive_packing_preserves_source_content_order() -> None:
    counter = TokenCounter("o200k_base")

    segments = [
        _segment(
            counter,
            "one.md",
            1,
            1,
            "# One\n\n" + ("alpha " * 1_500),
        ),
        _segment(
            counter,
            "two.md",
            1,
            1,
            "# Two\n\n" + ("beta " * 3_500),
        ),
    ]

    adaptive = pack_segments_adaptively(
        segments=segments,
        token_limit=3_000,
        encoding_name="o200k_base",
        token_counter=counter,
        minimum_split_search_tokens=128,
    )

    flattened = [segment for part in adaptive for segment in part]

    source_paths = [segment.source_path.as_posix() for segment in flattened]

    first_two_position = source_paths.index("two.md")

    assert all(source == "one.md" for source in source_paths[:first_two_position])
    assert all(source == "two.md" for source in source_paths[first_two_position:])

    assert all(
        segment.segment_index >= 1 and segment.segment_index <= segment.segment_count
        for segment in flattened
    )


def test_small_residual_capacity_does_not_force_tiny_split() -> None:
    counter = TokenCounter("o200k_base")

    segments = [
        _segment(
            counter,
            "one.md",
            1,
            1,
            "# One\n\n" + ("alpha " * 2_700),
        ),
        _segment(
            counter,
            "two.md",
            1,
            1,
            "# Two\n\n" + ("beta " * 1_000),
        ),
    ]

    adaptive = pack_segments_adaptively(
        segments=segments,
        token_limit=3_200,
        encoding_name="o200k_base",
        token_counter=counter,
        minimum_split_search_tokens=512,
    )

    assert adaptive
    assert all(part for part in adaptive)


def test_adaptive_packing_does_not_create_micro_fragments() -> None:
    counter = TokenCounter("o200k_base")
    minimum_fragment_tokens = 512

    segments = [
        _segment(
            counter,
            "first.md",
            1,
            1,
            "# First\n\n" + ("first content " * 1_900),
        ),
        _segment(
            counter,
            "second.md",
            1,
            2,
            "## Second A\n\n" + ("second alpha content " * 1_000),
        ),
        _segment(
            counter,
            "second.md",
            2,
            2,
            "## Second B\n\n" + ("second beta content " * 1_000),
        ),
    ]

    adaptive = pack_segments_adaptively(
        segments=segments,
        token_limit=4_000,
        encoding_name="o200k_base",
        token_counter=counter,
        minimum_split_search_tokens=minimum_fragment_tokens,
    )

    flattened = [segment for part in adaptive for segment in part]

    for segment in flattened:
        content_tokens = counter.count(segment.content)

        assert content_tokens >= minimum_fragment_tokens


def test_adaptive_split_keeps_small_remainder_unsplit() -> None:
    counter = TokenCounter("o200k_base")
    minimum_fragment_tokens = 512

    first = _segment(
        counter,
        "one.md",
        1,
        1,
        "# One\n\n" + ("alpha content " * 1_500),
    )

    second = _segment(
        counter,
        "two.md",
        1,
        1,
        "# Two\n\n" + ("beta content " * 1_100),
    )

    original_second_tokens = counter.count(second.content)

    adaptive = pack_segments_adaptively(
        segments=[first, second],
        token_limit=3_200,
        encoding_name="o200k_base",
        token_counter=counter,
        minimum_split_search_tokens=minimum_fragment_tokens,
    )

    second_segments = [
        segment for part in adaptive for segment in part if segment.source_path == Path("two.md")
    ]

    if len(second_segments) > 1:
        assert all(
            counter.count(segment.content) >= minimum_fragment_tokens for segment in second_segments
        )

        assert (
            sum(counter.count(segment.content) for segment in second_segments)
            >= original_second_tokens - 10
        )
