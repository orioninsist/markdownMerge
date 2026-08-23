from pathlib import Path

from markdown_merge.scanner import scan_markdown_files


def test_scan_markdown_files(tmp_path: Path):
    (tmp_path / "a.md").write_text("# Test", encoding="utf-8")

    files = scan_markdown_files(str(tmp_path))

    assert len(files) == 1
