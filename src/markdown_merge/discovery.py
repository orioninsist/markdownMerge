"""Recursive Markdown file discovery."""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Iterable
from pathlib import Path

from markdown_merge.models import MergeStatistics

MARKDOWN_SUFFIXES = {".md", ".markdown"}
IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "logs",
}

_NATURAL_PATTERN = re.compile(r"(\d+)")


def natural_sort_key(path: Path) -> tuple[tuple[object, ...], ...]:
    """Build a stable natural-sort key for a relative path."""
    components: list[tuple[object, ...]] = []

    for component in path.parts:
        pieces = _NATURAL_PATTERN.split(component.casefold())
        normalized: list[object] = []

        for piece in pieces:
            if piece.isdigit():
                normalized.append(int(piece))
            else:
                normalized.append(piece)

        components.append(tuple(normalized))

    return tuple(components)


def _should_ignore_directory(path: Path, output_directory: Path) -> bool:
    """Return whether a directory should be excluded from traversal."""
    try:
        if path.resolve() == output_directory.resolve():
            return True
    except OSError:
        pass

    return path.name in IGNORED_DIRECTORY_NAMES


def discover_markdown_files(
    input_directory: Path,
    output_directory: Path,
    statistics: MergeStatistics,
    logger: logging.Logger,
) -> list[Path]:
    """Recursively discover Markdown files under the input directory."""
    discovered: list[Path] = []

    for current_root, directory_names, file_names in os.walk(
        input_directory,
        topdown=True,
        followlinks=False,
    ):
        root = Path(current_root)
        statistics.directories_scanned += 1

        directory_names[:] = sorted(
            (
                name
                for name in directory_names
                if not _should_ignore_directory(root / name, output_directory)
                and not (root / name).is_symlink()
            ),
            key=str.casefold,
        )

        for filename in sorted(file_names, key=str.casefold):
            path = root / filename

            if path.is_symlink():
                logger.warning("Skipping symbolic link: %s", path)
                statistics.skipped_files += 1
                continue

            if path.suffix.casefold() in MARKDOWN_SUFFIXES:
                discovered.append(path)

    discovered.sort(key=lambda file_path: natural_sort_key(file_path.relative_to(input_directory)))

    statistics.discovered_markdown_files = len(discovered)
    logger.info(
        "Discovered %d Markdown files under %s",
        len(discovered),
        input_directory,
    )
    return discovered


def iter_parent_topics(relative_path: Path) -> Iterable[str]:
    """Yield normalized topic components for future grouping extensions."""
    for part in relative_path.parent.parts:
        if part not in {".", ""}:
            yield part.casefold()
