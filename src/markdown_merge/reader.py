"""Safe Markdown source reader."""

from __future__ import annotations

import logging
from pathlib import Path

from markdown_merge.cleaner import clean_markdown
from markdown_merge.models import MergeStatistics, SourceDocument
from markdown_merge.tokenizer import TokenCounter

ENCODING_CANDIDATES = (
    "utf-8",
    "utf-8-sig",
    "utf-16",
    "cp1252",
    "latin-1",
)


def _read_text_with_fallback(path: Path) -> tuple[str, str]:
    """Read text using deterministic encoding fallbacks."""
    last_error: UnicodeError | None = None

    for encoding in ENCODING_CANDIDATES:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeError as error:
            last_error = error

    if last_error is not None:
        raise last_error

    raise UnicodeError(f"Unable to decode file: {path}")


def read_source_document(
    path: Path,
    input_directory: Path,
    token_counter: TokenCounter,
    statistics: MergeStatistics,
    logger: logging.Logger,
) -> SourceDocument | None:
    """Read, clean, and tokenize one Markdown source file."""
    try:
        raw_text, encoding = _read_text_with_fallback(path)
    except (OSError, UnicodeError) as error:
        statistics.failed_files += 1
        message = f"Failed to read {path}: {error}"
        statistics.warnings.append(message)
        logger.exception(message)
        return None

    cleaned = clean_markdown(raw_text)
    relative_path = path.relative_to(input_directory)

    if not cleaned:
        statistics.skipped_files += 1
        message = f"Skipping empty document after cleaning: {relative_path}"
        statistics.warnings.append(message)
        logger.warning(message)
        return None

    token_count = token_counter.count(cleaned)

    statistics.processed_source_files += 1
    statistics.original_characters += len(raw_text)
    statistics.cleaned_characters += len(cleaned)
    statistics.source_tokens += token_count

    logger.debug(
        "Read source=%s encoding=%s original_chars=%d cleaned_chars=%d tokens=%d",
        relative_path,
        encoding,
        len(raw_text),
        len(cleaned),
        token_count,
    )

    return SourceDocument(
        absolute_path=path,
        relative_path=relative_path,
        content=cleaned,
        original_characters=len(raw_text),
        cleaned_characters=len(cleaned),
        content_tokens=token_count,
    )
