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


def test_split_files_uses_first_fit_decreasing(tmp_path: Path) -> None:
    files: list[Path] = []
    for name, repeats in [
        ("a.md", 60),
        ("b.md", 60),
        ("c.md", 40),
        ("d.md", 40),
    ]:
        file = tmp_path / name
        file.write_text(("word " * repeats).strip(), encoding="utf-8")
        files.append(file)

    probe = split_files(
        files,
        10_000,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )
    weights = {
        chunk.source_path: chunk.tokens for part in probe for chunk in part.files
    }
    capacity = max(
        weights["a.md"] + weights["c.md"],
        weights["b.md"] + weights["d.md"],
    )

    parts = split_files(
        files,
        capacity,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    assert len(parts) == 2
    assert {chunk.source_path for chunk in parts[0].files} == {"a.md", "c.md"}
    assert {chunk.source_path for chunk in parts[1].files} == {"b.md", "d.md"}


def test_split_files_is_deterministic_for_equal_sizes(tmp_path: Path) -> None:
    files = []
    for name in ["c.md", "a.md", "b.md"]:
        file = tmp_path / name
        file.write_text("same content", encoding="utf-8")
        files.append(file)

    parts = split_files(
        files,
        10_000,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    assert [chunk.source_path for chunk in parts[0].files] == [
        "a.md",
        "b.md",
        "c.md",
    ]
