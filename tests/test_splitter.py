from pathlib import Path

import pytest

from markdown_merge.splitter import split_files


def test_split_files(tmp_path: Path) -> None:
    file = tmp_path / "test.md"
    file.write_text("# Test\ncontent", encoding="utf-8")

    parts = split_files([file], 100, reserve_tokens=0)

    assert len(parts) == 1
    assert len(parts[0].files) == 1


def test_split_files_uses_relative_source_paths(tmp_path: Path) -> None:
    nested = tmp_path / "guides"
    nested.mkdir()
    file = nested / "setup.md"
    file.write_text("# Setup", encoding="utf-8")

    parts = split_files(
        [file],
        100,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    assert parts[0].files[0].source_path == "guides/setup.md"


def test_split_files_rejects_oversized_source(tmp_path: Path) -> None:
    file = tmp_path / "large.md"
    file.write_text("token " * 100, encoding="utf-8")

    with pytest.raises(ValueError, match="exceeds the effective token limit"):
        split_files([file], 10, reserve_tokens=0)


def test_split_files_rejects_invalid_reserve() -> None:
    with pytest.raises(ValueError, match="smaller than token_limit"):
        split_files([], 100, reserve_tokens=100)
