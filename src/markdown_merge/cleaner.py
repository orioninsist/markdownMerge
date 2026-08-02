"""Markdown and embedded HTML cleaning."""

from __future__ import annotations

import html
import re

_BASE64_MARKDOWN_IMAGE = re.compile(
    r"!\[[^\]]*]\(\s*data:image/[^;()\s]+;base64,[A-Za-z0-9+/=\s]+\s*\)",
    flags=re.IGNORECASE,
)
_BASE64_HTML_IMAGE = re.compile(
    r"<img\b[^>]*\bsrc\s*=\s*"
    r"(?:\"data:image/[^;]+;base64,[^\"]+\"|'data:image/[^;]+;base64,[^']+')"
    r"[^>]*>",
    flags=re.IGNORECASE | re.DOTALL,
)
_DATA_URI = re.compile(
    r"data:image/[A-Za-z0-9.+-]+;base64,[A-Za-z0-9+/=\s]{100,}",
    flags=re.IGNORECASE,
)
_HTML_COMMENTS = re.compile(r"<!--.*?-->", flags=re.DOTALL)
_EXCESSIVE_BLANK_LINES = re.compile(r"\n[ \t]*\n(?:[ \t]*\n)+")
_TRAILING_WHITESPACE = re.compile(r"[ \t]+$", flags=re.MULTILINE)
_BROKEN_ORPHAN_TAGS = re.compile(
    r"(?mi)^[ \t]*(?:</?(?:div|span|section|article|main|aside|header|footer|"
    r"nav|table|tbody|thead|tfoot|tr|td|th|ul|ol|li|p|br|hr|details|summary)"
    r"(?:\s+[^<>]*)?>?)[ \t]*$"
)
_EMPTY_HTML_PAIRS = re.compile(
    r"<(?P<tag>div|span|section|article|p|strong|em|b|i)\b[^>]*>"
    r"\s*</(?P=tag)>",
    flags=re.IGNORECASE,
)
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def _normalize_newlines(text: str) -> str:
    """Normalize all line endings to LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _remove_unbalanced_comment_markers(text: str) -> str:
    """Remove isolated HTML comment delimiters."""
    return text.replace("<!--", "").replace("-->", "")


def clean_markdown(text: str) -> str:
    """Clean noisy Markdown while preserving meaningful source content."""
    cleaned = _normalize_newlines(text)
    cleaned = cleaned.lstrip("\ufeff")
    cleaned = _CONTROL_CHARACTERS.sub("", cleaned)

    cleaned = _BASE64_MARKDOWN_IMAGE.sub(
        "\n\n> [Embedded image removed]\n\n",
        cleaned,
    )
    cleaned = _BASE64_HTML_IMAGE.sub(
        "\n\n> [Embedded image removed]\n\n",
        cleaned,
    )
    cleaned = _DATA_URI.sub("[embedded image data removed]", cleaned)

    cleaned = _HTML_COMMENTS.sub("", cleaned)
    cleaned = _remove_unbalanced_comment_markers(cleaned)
    cleaned = _EMPTY_HTML_PAIRS.sub("", cleaned)

    # Remove lines that contain only common orphaned structural HTML tags.
    # Inline semantic HTML containing useful text remains untouched.
    cleaned = _BROKEN_ORPHAN_TAGS.sub("", cleaned)

    cleaned = html.unescape(cleaned)
    cleaned = _TRAILING_WHITESPACE.sub("", cleaned)
    cleaned = _EXCESSIVE_BLANK_LINES.sub("\n\n", cleaned)

    return cleaned.strip()
