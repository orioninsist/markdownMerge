from pathlib import Path

from markdown_merge.splitter import split_files
from markdown_merge.writer import write_parts


def test_write_parts_uses_semantic_filename(tmp_path: Path) -> None:
    source = tmp_path / "authentication.md"
    source.write_text("# Authentication", encoding="utf-8")

    output = tmp_path / "output"
    parts = split_files(
        [source],
        100,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    files = write_parts(parts, str(output), str(tmp_path))

    assert files == [output / "authentication.md"]
    assert files[0].exists()


def test_write_parts_uses_topics_from_multiple_sources(tmp_path: Path) -> None:
    docs = tmp_path / "api"
    docs.mkdir()
    auth = docs / "authentication.md"
    tokens = docs / "tokens.md"
    auth.write_text("# Authentication", encoding="utf-8")
    tokens.write_text("# Tokens", encoding="utf-8")

    output = tmp_path / "output"
    parts = split_files(
        [auth, tokens],
        1000,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    files = write_parts(parts, str(output), str(tmp_path))

    assert files == [output / "authentication-tokens.md"]


def test_write_parts_uses_common_directory_for_generic_sources(tmp_path: Path) -> None:
    guides = tmp_path / "security"
    guides.mkdir()
    index = guides / "index.md"
    readme = guides / "readme.md"
    index.write_text("# Index", encoding="utf-8")
    readme.write_text("# Readme", encoding="utf-8")

    output = tmp_path / "output"
    parts = split_files(
        [index, readme],
        1000,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    files = write_parts(parts, str(output), str(tmp_path))

    assert files == [output / "security.md"]


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

    files = write_parts(parts, str(output), str(tmp_path))
    content = files[0].read_text(encoding="utf-8")

    assert "# Source: guides/setup.md" in content


def test_duplicate_semantic_names_get_deterministic_suffixes(tmp_path: Path) -> None:
    first_dir = tmp_path / "one"
    second_dir = tmp_path / "two"
    first_dir.mkdir()
    second_dir.mkdir()

    first = first_dir / "authentication.md"
    second = second_dir / "authentication.md"
    first.write_text("# Authentication one", encoding="utf-8")
    second.write_text("# Authentication two", encoding="utf-8")

    output = tmp_path / "output"
    parts = split_files(
        [first, second],
        20,
        input_directory=str(tmp_path),
        reserve_tokens=0,
    )

    files = write_parts(parts, str(output), str(tmp_path))

    assert [file.name for file in files] == [
        "authentication.md",
        "authentication-2.md",
    ]
