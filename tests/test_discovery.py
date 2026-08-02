"""Tests for recursive Markdown discovery."""

import logging
from pathlib import Path

from markdown_merge.discovery import discover_markdown_files
from markdown_merge.models import MergeStatistics


def test_discovery_is_recursive_and_markdown_only(tmp_path: Path) -> None:
    input_directory = tmp_path / "input"
    output_directory = tmp_path / "output"
    nested_directory = input_directory / "guide"

    nested_directory.mkdir(parents=True)
    output_directory.mkdir()

    (input_directory / "10-last.md").write_text("last", encoding="utf-8")
    (input_directory / "2-middle.md").write_text("middle", encoding="utf-8")
    (nested_directory / "1-first.markdown").write_text("first", encoding="utf-8")
    (nested_directory / "ignored.txt").write_text("ignored", encoding="utf-8")

    statistics = MergeStatistics()
    files = discover_markdown_files(
        input_directory=input_directory,
        output_directory=output_directory,
        statistics=statistics,
        logger=logging.getLogger("test-discovery"),
    )

    relative_files = [path.relative_to(input_directory).as_posix() for path in files]

    assert relative_files == [
        "2-middle.md",
        "10-last.md",
        "guide/1-first.markdown",
    ]
    assert statistics.discovered_markdown_files == 3
