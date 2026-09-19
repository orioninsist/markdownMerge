from pathlib import Path

from markdown_merge.validator import validate_output


def test_validator_passes_valid_output(tmp_path: Path) -> None:
    file = tmp_path / "part_001.md"
    file.write_text("# Source: test.md\n\n# Test", encoding="utf-8")

    result = validate_output(str(tmp_path), 100)

    assert result.passed is True
    assert "PASSED" in result.report


def test_validator_fails_when_token_limit_is_exceeded(tmp_path: Path) -> None:
    file = tmp_path / "part_001.md"
    file.write_text("# Source: test.md\n\n" + ("token " * 100), encoding="utf-8")

    result = validate_output(str(tmp_path), 10)

    assert result.passed is False
    assert "token limit exceeded" in result.report
    assert "Validation Result: FAILED" in result.report


def test_validator_fails_when_source_markers_are_missing(tmp_path: Path) -> None:
    file = tmp_path / "part_001.md"
    file.write_text("# Test", encoding="utf-8")

    result = validate_output(str(tmp_path), 100)

    assert result.passed is False
    assert "no source markers found" in result.report
