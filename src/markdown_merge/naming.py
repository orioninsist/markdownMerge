"""Generic content-aware output filename generation."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

_TITLE_PATTERNS = (
    re.compile(r"(?mi)^title\s*:\s*[\"']?(.+?)[\"']?\s*$"),
    re.compile(r"(?m)^#\s+(.+?)\s*$"),
    re.compile(r"(?m)^##\s+(.+?)\s*$"),
)

_WORD_PATTERN = re.compile(r"[A-Za-z0-9]+")

_GENERIC_DIRECTORY_NAMES = {
    "archive",
    "content",
    "data",
    "doc",
    "docs",
    "document",
    "documents",
    "documentation",
    "export",
    "files",
    "input",
    "markdown",
    "output",
    "pages",
    "source",
    "sources",
}

_STOP_WORDS = {
    "a",
    "about",
    "all",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "bir",
    "bu",
    "by",
    "da",
    "de",
    "for",
    "from",
    "how",
    "ile",
    "in",
    "is",
    "it",
    "icin",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "this",
    "to",
    "ve",
    "with",
    "you",
    "your",
}

_PRESERVED_ACRONYMS = {
    "ai": "AI",
    "api": "API",
    "cli": "CLI",
    "css": "CSS",
    "faq": "FAQ",
    "html": "HTML",
    "http": "HTTP",
    "https": "HTTPS",
    "json": "JSON",
    "sdk": "SDK",
    "sql": "SQL",
    "ui": "UI",
    "url": "URL",
    "xml": "XML",
}


def _ascii_text(value: str) -> str:
    """Convert Unicode text into safe ASCII text."""
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _words(value: str) -> list[str]:
    """Extract normalized words from arbitrary text."""
    return [word.casefold() for word in _WORD_PATTERN.findall(_ascii_text(value)) if word]


def _display_word(word: str) -> str:
    """Convert one normalized word into a filename component."""
    preserved = _PRESERVED_ACRONYMS.get(word.casefold())

    if preserved is not None:
        return preserved

    return word[:1].upper() + word[1:].lower()


def _unique_words(words: Iterable[str]) -> list[str]:
    """Return words without case-insensitive duplicates."""
    result: list[str] = []
    seen: set[str] = set()

    for word in words:
        normalized = word.casefold()

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        result.append(word)

    return result


def _read_sample(path: Path, maximum_characters: int = 120_000) -> str:
    """Read a bounded Markdown sample using safe encoding fallbacks."""
    encodings = (
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "cp1252",
        "latin-1",
    )

    for encoding in encodings:
        try:
            with path.open("r", encoding=encoding) as handle:
                return handle.read(maximum_characters)
        except (OSError, UnicodeError):
            continue

    return ""


def _extract_titles(text: str) -> list[str]:
    """Extract frontmatter titles and Markdown headings."""
    titles: list[str] = []

    for pattern in _TITLE_PATTERNS:
        for match in pattern.finditer(text):
            title = match.group(1).strip().strip("\"'`# ")

            if title:
                titles.append(title)

            if len(titles) >= 40:
                return titles

    return titles


def _directory_identity(input_directory: Path) -> list[str]:
    """Extract a meaningful identity from the input directory name."""
    directory_words = _words(input_directory.resolve().name)

    useful = [
        word
        for word in directory_words
        if word not in _GENERIC_DIRECTORY_NAMES and word not in _STOP_WORDS and not word.isdigit()
    ]

    return useful[:3]


def _title_phrase_candidates(
    titles_by_document: list[list[str]],
) -> Counter[tuple[str, ...]]:
    """Count meaningful repeated phrases across document titles."""
    frequencies: Counter[tuple[str, ...]] = Counter()

    for document_titles in titles_by_document:
        document_phrases: set[tuple[str, ...]] = set()

        for title in document_titles:
            title_words = [word for word in _words(title) if not word.isdigit()]

            for size in range(2, min(5, len(title_words) + 1)):
                for start in range(0, len(title_words) - size + 1):
                    phrase = tuple(title_words[start : start + size])

                    meaningful_words = [word for word in phrase if word not in _STOP_WORDS]

                    if len(meaningful_words) < 2:
                        continue

                    document_phrases.add(phrase)

        frequencies.update(document_phrases)

    return frequencies


def _single_word_candidates(
    titles_by_document: list[list[str]],
) -> Counter[str]:
    """Count meaningful title words by document frequency."""
    frequencies: Counter[str] = Counter()

    for document_titles in titles_by_document:
        document_words: set[str] = set()

        for title in document_titles:
            for word in _words(title):
                if (
                    len(word) >= 3
                    and word not in _STOP_WORDS
                    and word not in _GENERIC_DIRECTORY_NAMES
                    and not word.isdigit()
                ):
                    document_words.add(word)

        frequencies.update(document_words)

    return frequencies


def _select_best_phrase(
    titles_by_document: list[list[str]],
    base_words: list[str],
) -> list[str]:
    """Select the strongest repeated phrase from source headings."""
    document_count = max(1, len(titles_by_document))
    required_frequency = 1 if document_count == 1 else max(2, math.ceil(document_count * 0.12))

    phrase_frequencies = _title_phrase_candidates(titles_by_document)
    base_set = {word.casefold() for word in base_words}

    scored_phrases: list[tuple[int, tuple[str, ...]]] = []

    for phrase, frequency in phrase_frequencies.items():
        if frequency < required_frequency:
            continue

        non_base_words = [
            word for word in phrase if word.casefold() not in base_set and word not in _STOP_WORDS
        ]

        if not non_base_words:
            continue

        score = frequency * 1_000 + len(non_base_words) * 100 + len(phrase) * 10

        scored_phrases.append((score, phrase))

    if scored_phrases:
        scored_phrases.sort(
            key=lambda item: (
                item[0],
                len(item[1]),
                item[1],
            ),
            reverse=True,
        )
        return list(scored_phrases[0][1])

    word_frequencies = _single_word_candidates(titles_by_document)

    fallback_words = [
        word
        for word, frequency in word_frequencies.most_common()
        if frequency >= required_frequency and word.casefold() not in base_set
    ]

    return fallback_words[:2]


def derive_output_prefix(
    input_directory: Path,
    markdown_files: list[Path],
) -> str:
    """Generate a general smart prefix by analyzing the Markdown corpus."""
    base_words = _directory_identity(input_directory)
    titles_by_document: list[list[str]] = []

    for path in markdown_files[:500]:
        sample = _read_sample(path)

        if not sample:
            continue

        titles = _extract_titles(sample)

        if titles:
            titles_by_document.append(titles)

    selected_phrase = _select_best_phrase(
        titles_by_document=titles_by_document,
        base_words=base_words,
    )

    combined_words = _unique_words(
        [
            *base_words,
            *selected_phrase,
        ]
    )

    if not combined_words:
        combined_words = ["merged", "markdown"]

    display_words = [_display_word(word) for word in combined_words[:6]]

    prefix = "_".join(display_words)
    prefix = re.sub(r"_+", "_", prefix).strip("_")

    return prefix[:100] or "Merged_Markdown"
