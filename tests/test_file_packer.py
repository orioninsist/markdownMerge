from pathlib import Path

import pytest

from markdown_merge.file_packer import pack_files
from markdown_merge.models import DocumentSegment


def _segment(
    source: str,
    tokens: int,
) -> DocumentSegment:
    return DocumentSegment(
        source_path=Path(source),
        segment_index=1,
        segment_count=1,
        content="content",
        rendered_content="content",
        token_count=tokens,
    )


def test_file_packer_keeps_files_under_token_limit() -> None:
    segments = [
        _segment("001.md", 1000),
        _segment("002.md", 2000),
        _segment("003.md", 1500),
    ]

    parts = pack_files(
        segments=segments,
        token_limit=4000,
    )

    assert len(parts) == 2
    assert parts[0].token_count == 3000
    assert parts[1].token_count == 1500


def test_file_packer_preserves_source_order() -> None:
    segments = [
        _segment("001.md", 100),
        _segment("002.md", 100),
        _segment("003.md", 100),
    ]

    parts = pack_files(
        segments=segments,
        token_limit=500,
    )

    assert [segment.source_path.name for segment in parts[0].segments] == [
        "001.md",
        "002.md",
        "003.md",
    ]


def test_file_packer_rejects_single_large_file() -> None:
    segments = [
        _segment("large.md", 5000),
    ]

    with pytest.raises(
        RuntimeError,
        match="Single markdown source exceeds token limit",
    ):
        pack_files(
            segments=segments,
            token_limit=1000,
        )


def test_file_packer_rejects_invalid_limit() -> None:
    with pytest.raises(
        ValueError,
        match="token_limit must be positive",
    ):
        pack_files(
            segments=[],
            token_limit=0,
        )
