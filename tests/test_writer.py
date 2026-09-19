from pathlib import Path

from markdown_merge.splitter import split_files
from markdown_merge.writer import _get_source_name, write_parts


def test_source_name_when_input_ends_with_docs() -> None:
    source_name = _get_source_name("/mnt/local/resources/google/docs")

    assert source_name == "google"


def test_source_name_from_first_directory_after_docs() -> None:
    source_name = _get_source_name("/mnt/local/resources/google/docs/adsense")

    assert source_name == "adsense"


def test_source_name_ignores_deeper_directories_after_docs() -> None:
    source_name = _get_source_name(
        "/mnt/local/resources/google/docs/adsense/reference/api"
    )

    assert source_name == "adsense"


def test_source_name_for_openai_docs() -> None:
    source_name = _get_source_name("/mnt/local/resources/openai/docs")

    assert source_name == "openai"


def test_source_name_for_directory_without_docs() -> None:
    source_name = _get_source_name("/mnt/local/resources/example")

    assert source_name == "example"


def test_write_parts_uses_input_derived_filename(tmp_path: Path) -> None:
    source = tmp_path / "test.md"
    source.write_text("# Test", encoding="utf-8")

    output = tmp_path / "output"
    parts = split_files([source], 100, reserve_tokens=0)

    files = write_parts(
        parts,
        str(output),
        "/mnt/local/resources/google/docs",
    )

    assert files == [output / "google-1.md"]
    assert files[0].exists()


def test_write_parts_uses_directory_after_docs(tmp_path: Path) -> None:
    source = tmp_path / "test.md"
    source.write_text("# Test", encoding="utf-8")

    output = tmp_path / "output"
    parts = split_files([source], 100, reserve_tokens=0)

    files = write_parts(
        parts,
        str(output),
        "/mnt/local/resources/google/docs/adsense",
    )

    assert files == [output / "adsense-1.md"]
    assert files[0].exists()


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
