"""Tests for atomic output writing and generated-file cleanup."""

from pathlib import Path

from markdown_merge.writer import cleanup_previous_output_parts


def test_cleanup_previous_output_parts_removes_only_generated_parts(
    tmp_path: Path,
) -> None:
    generated = tmp_path / "Docs_Part_01_of_03.md"
    generated.write_text("generated", encoding="utf-8")

    unrelated_markdown = tmp_path / "notes.md"
    unrelated_markdown.write_text("keep", encoding="utf-8")

    manifest = tmp_path / "merge_manifest.json"
    manifest.write_text("{}", encoding="utf-8")

    removed = cleanup_previous_output_parts(tmp_path)

    assert removed == [generated]
    assert not generated.exists()
    assert unrelated_markdown.exists()
    assert manifest.exists()
