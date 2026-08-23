"""Atomic output and manifest writing."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import Any

from markdown_merge.models import (
    DocumentSegment,
    MergeStatistics,
    OutputPart,
    ProgressUpdate,
)
from markdown_merge.renderer import render_document
from markdown_merge.tokenizer import TokenCounter

WriterProgressCallback = Callable[[ProgressUpdate], None]


def _noop_progress(update: ProgressUpdate) -> None:
    """Default writer progress callback."""
    del update


_GENERATED_PART_PATTERN = re.compile(
    r"^.+_Part_\d+_of_\d+\.md$",
    flags=re.IGNORECASE,
)


def cleanup_previous_output_parts(output_directory: Path) -> list[Path]:
    """Remove generated Markdown parts left by previous merge runs."""
    removed: list[Path] = []

    if not output_directory.exists():
        return removed

    for candidate in output_directory.iterdir():
        if not candidate.is_file():
            continue

        if not _GENERATED_PART_PATTERN.fullmatch(candidate.name):
            continue

        candidate.unlink()
        removed.append(candidate)

    return removed


def atomic_write_text(path: Path, content: str) -> None:
    """Write a text file atomically in the target directory."""
    path.parent.mkdir(parents=True, exist_ok=True)

    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )

    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_name, path)
    except BaseException:
        with suppress(FileNotFoundError):
            os.unlink(temporary_name)
        raise


def _sha256(content: str) -> str:
    """Return a SHA-256 checksum for text content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def write_output_parts(
    packed_parts: list[list[DocumentSegment]],
    output_directory: Path,
    output_prefix: str,
    token_limit: int | None,
    encoding_name: str,
    token_counter: TokenCounter,
    progress_callback: WriterProgressCallback = _noop_progress,
) -> list[OutputPart]:
    """Render and atomically write all merged output parts."""
    output_directory.mkdir(parents=True, exist_ok=True)
    cleanup_previous_output_parts(output_directory)
    output_parts: list[OutputPart] = []

    total_parts = len(packed_parts)
    width = max(2, len(str(total_parts)))

    for part_number, segments in enumerate(packed_parts, start=1):
        filename = f"{output_prefix}_Part_{part_number:0{width}d}_of_{total_parts:0{width}d}.md"
        path = output_directory / filename

        progress_callback(
            ProgressUpdate(
                stage="Writing output parts",
                completed=part_number - 1,
                total=total_parts,
                detail=filename,
                current_part=part_number,
                token_limit=token_limit,
            )
        )

        document = render_document(
            part_number=part_number,
            segments=segments,
            token_limit=token_limit,
            encoding_name=encoding_name,
            token_counter=token_counter,
        )
        token_count = token_counter.count(document)

        if token_limit is not None and token_count > token_limit:
            raise RuntimeError(
                f"Refusing to write {filename}: {token_count:,} tokens exceeds {token_limit:,}."
            )

        atomic_write_text(path, document)

        output_parts.append(
            OutputPart(
                part_number=part_number,
                filename=filename,
                path=path,
                token_count=token_count,
                character_count=len(document),
                segments=tuple(segments),
                sha256=_sha256(document),
            )
        )

        progress_callback(
            ProgressUpdate(
                stage="Writing output parts",
                completed=part_number,
                total=total_parts,
                detail=filename,
                current_part=part_number,
                current_tokens=token_count,
                token_limit=token_limit,
            )
        )

    return output_parts


def write_manifest(
    output_directory: Path,
    input_directory: Path,
    output_parts: list[OutputPart],
    statistics: MergeStatistics,
    token_limit: int | None,
    encoding_name: str,
) -> Path:
    """Write a JSON manifest describing every output and source mapping."""
    manifest_path = output_directory / "merge_manifest.json"

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "input_directory": str(input_directory),
        "output_directory": str(output_directory),
        "encoding": encoding_name,
        "token_limit": token_limit,
        "statistics": {
            "directories_scanned": statistics.directories_scanned,
            "discovered_markdown_files": statistics.discovered_markdown_files,
            "processed_source_files": statistics.processed_source_files,
            "skipped_files": statistics.skipped_files,
            "failed_files": statistics.failed_files,
            "original_characters": statistics.original_characters,
            "cleaned_characters": statistics.cleaned_characters,
            "removed_characters": statistics.removed_characters,
            "source_tokens": statistics.source_tokens,
            "output_tokens": statistics.output_tokens,
            "output_parts": statistics.output_parts,
            "oversized_sources_split": statistics.oversized_sources_split,
            "generated_segments": statistics.generated_segments,
            "warnings": statistics.warnings,
        },
        "parts": [
            {
                "part_number": part.part_number,
                "filename": part.filename,
                "path": str(part.path),
                "token_count": part.token_count,
                "character_count": part.character_count,
                "sha256": part.sha256,
                "sources": [
                    {
                        "source_path": segment.source_path.as_posix(),
                        "segment_index": segment.segment_index,
                        "segment_count": segment.segment_count,
                        "rendered_token_count": segment.token_count,
                    }
                    for segment in part.segments
                ],
            }
            for part in output_parts
        ],
    }

    atomic_write_text(
        manifest_path,
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
    )
    return manifest_path
