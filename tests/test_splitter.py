from pathlib import Path

from markdown_merge.splitter import split_files


def test_split_files(tmp_path: Path):
    file = tmp_path / "test.md"
    file.write_text("# Test\ncontent", encoding="utf-8")

    parts = split_files([file], 100)

    assert len(parts) == 1
    assert len(parts[0].files) == 1
