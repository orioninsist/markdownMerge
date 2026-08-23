from pathlib import Path

from markdown_merge.splitter import split_files
from markdown_merge.writer import write_parts


def test_write_parts(tmp_path: Path):
    source = tmp_path / "test.md"
    source.write_text("# Test", encoding="utf-8")

    output = tmp_path / "output"

    parts = split_files([source], 100)

    files = write_parts(parts, str(output))

    assert files[0].exists()
