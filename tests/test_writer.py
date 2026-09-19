from pathlib import Path

from markdown_merge.splitter import split_files
from markdown_merge.writer import write_parts


def test_write_parts_uses_user_supplied_name(tmp_path: Path) -> None:
    source = tmp_path / "authentication.md"
    source.write_text("# Authentication", encoding="utf-8")

    output = tmp_path / "output"
    parts = split_files(
        [source],
        100,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    files = write_parts(parts, str(output), str(tmp_path), "openai")

    assert files == [output / "openai-1.md"]
    assert files[0].exists()


def test_write_parts_numbers_multiple_parts(tmp_path: Path) -> None:
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("# First " + "word " * 30, encoding="utf-8")
    second.write_text("# Second " + "word " * 30, encoding="utf-8")

    output = tmp_path / "output"
    parts = split_files(
        [first, second],
        50,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    files = write_parts(parts, str(output), str(tmp_path), "docs")

    assert [file.name for file in files] == ["docs-1.md", "docs-2.md"]


def test_write_parts_writes_relative_source_marker(tmp_path: Path) -> None:
    nested = tmp_path / "guides"
    nested.mkdir()
    source = nested / "setup.md"
    source.write_text("# Setup", encoding="utf-8")

    output = tmp_path / "output"
    parts = split_files(
        [source],
        100,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    files = write_parts(parts, str(output), str(tmp_path), "guide")
    content = files[0].read_text(encoding="utf-8")

    assert files[0].name == "guide-1.md"
    assert "# Source: guides/setup.md" in content
