from pathlib import Path

from markdown_merge.validator import validate_output


def test_validator(tmp_path: Path):
    file = tmp_path / "part_001.md"
    file.write_text("# Source: test.md\n\n# Test", encoding="utf-8")

    result = validate_output(str(tmp_path), 100)

    assert "PASSED" in result
