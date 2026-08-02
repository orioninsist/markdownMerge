"""Tests for Markdown cleaning."""

from markdown_merge.cleaner import clean_markdown


def test_clean_markdown_reduces_excessive_blank_lines() -> None:
    source = "First\n\n\n\n\nSecond"
    assert clean_markdown(source) == "First\n\nSecond"


def test_clean_markdown_removes_base64_markdown_image() -> None:
    source = "# Title\n\n![image](data:image/png;base64," + ("A" * 300) + ")\n\nText"
    result = clean_markdown(source)

    assert "base64" not in result.casefold()
    assert "Embedded image removed" in result
    assert "Text" in result


def test_clean_markdown_preserves_inline_html_with_text() -> None:
    source = "Before <strong>important</strong> after"
    assert clean_markdown(source) == source
