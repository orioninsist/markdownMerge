"""Application service orchestrating the complete merge workflow."""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

from markdown_merge.config import MergeConfig
from markdown_merge.discovery import discover_markdown_files
from markdown_merge.models import (
    DocumentSegment,
    MergeResult,
    MergeStatistics,
    ProgressUpdate,
)
from markdown_merge.naming import derive_output_prefix
from markdown_merge.packer import pack_segments
from markdown_merge.reader import read_source_document
from markdown_merge.splitter import split_source_document
from markdown_merge.tokenizer import TokenCounter
from markdown_merge.writer import write_manifest, write_output_parts

ProgressCallback = Callable[[ProgressUpdate], None]

DEFAULT_SOURCE_SEGMENT_TOKENS = 80_000
DEFAULT_OUTPUT_PART_TOKENS = 250_000


def _noop_progress(update: ProgressUpdate) -> None:
    """Default progress callback."""
    del update


def _runtime_progress(
    started_at: float,
    completed: int,
    total: int,
) -> tuple[float, float | None, float | None]:
    """Calculate elapsed time, speed, and ETA."""
    elapsed = perf_counter() - started_at

    if elapsed <= 0 or completed <= 0:
        return elapsed, None, None

    speed = completed / elapsed
    remaining = max(total - completed, 0)

    eta = remaining / speed if speed > 0 else None

    return elapsed, speed, eta


def _make_progress(
    started_at: float,
    stage: str,
    completed: int,
    total: int,
    detail: str = "",
    current_source: str | None = None,
    current_part: int | None = None,
    current_tokens: int | None = None,
    token_limit: int | None = None,
) -> ProgressUpdate:
    """Create progress updates with runtime information."""
    elapsed, speed, eta = _runtime_progress(
        started_at,
        completed,
        total,
    )

    return ProgressUpdate(
        stage=stage,
        completed=completed,
        total=total,
        detail=detail,
        current_source=current_source,
        current_part=current_part,
        current_tokens=current_tokens,
        token_limit=token_limit,
        elapsed_seconds=elapsed,
        items_per_second=speed,
        eta_seconds=eta,
    )


class MarkdownMergeService:
    """Coordinate discovery, cleaning, splitting, packing, and output."""

    def __init__(
        self,
        config: MergeConfig,
        logger: logging.Logger,
        log_path: Path,
    ) -> None:
        self._config = config
        self._logger = logger
        self._log_path = log_path
        self._token_counter = TokenCounter(config.encoding_name)

    def execute(
        self,
        progress_callback: ProgressCallback = _noop_progress,
    ) -> MergeResult:
        """Execute the full Markdown merge operation."""
        started_at = perf_counter()
        statistics = MergeStatistics()

        self._config.validate()
        self._config.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._logger.info(
            "Merge started input=%s output=%s token_limit=%d encoding=%s",
            self._config.input_directory,
            self._config.output_directory,
            self._config.token_limit,
            self._config.encoding_name,
        )

        files = discover_markdown_files(
            input_directory=self._config.input_directory,
            output_directory=self._config.output_directory,
            statistics=statistics,
            logger=self._logger,
        )

        if not files:
            raise FileNotFoundError(
                f"No Markdown files found under: {self._config.input_directory}"
            )

        resolved_output_prefix = (
            self._config.output_prefix.strip()
            if self._config.output_prefix
            else derive_output_prefix(
                self._config.input_directory,
                files,
            )
        )

        self._logger.info(
            "Resolved content-aware output prefix: %s",
            resolved_output_prefix,
        )

        all_segments: list[DocumentSegment] = []
        segment_budget = (
            self._config.token_limit - self._config.toc_reserve_tokens
            if self._config.token_limit is not None
            else DEFAULT_SOURCE_SEGMENT_TOKENS
        )

        for index, path in enumerate(files, start=1):
            relative_path = path.relative_to(self._config.input_directory)

            progress_callback(
                _make_progress(
                    started_at=started_at,
                    stage="Processing Markdown sources",
                    completed=index - 1,
                    total=len(files),
                    detail=relative_path.as_posix(),
                    current_source=relative_path.as_posix(),
                    token_limit=self._config.token_limit,
                )
            )

            document = read_source_document(
                path=path,
                input_directory=self._config.input_directory,
                token_counter=self._token_counter,
                statistics=statistics,
                logger=self._logger,
            )

            if document is None:
                progress_callback(
                    _make_progress(
                        started_at=started_at,
                        stage="Processing Markdown sources",
                        completed=index,
                        total=len(files),
                        detail=relative_path.as_posix(),
                        current_source=relative_path.as_posix(),
                        token_limit=self._config.token_limit,
                    )
                )
                continue

            if segment_budget is None:
                segments = [
                    DocumentSegment(
                        source_path=document.relative_path,
                        segment_index=1,
                        segment_count=1,
                        content=document.content,
                        rendered_content=document.content,
                        token_count=document.content_tokens,
                    )
                ]
            else:
                segments = split_source_document(
                    document=document,
                    token_budget=segment_budget,
                    token_counter=self._token_counter,
                    minimum_split_search_tokens=(self._config.minimum_split_search_tokens),
                )

            if len(segments) > 1:
                statistics.oversized_sources_split += 1
                self._logger.info(
                    "Split oversized source %s into %d segments",
                    relative_path,
                    len(segments),
                )

            all_segments.extend(segments)

            progress_callback(
                _make_progress(
                    started_at=started_at,
                    stage="Processing Markdown sources",
                    completed=index,
                    total=len(files),
                    detail=relative_path.as_posix(),
                    current_source=relative_path.as_posix(),
                    token_limit=self._config.token_limit,
                )
            )

        if not all_segments:
            raise RuntimeError("Markdown files were discovered, but none contained usable content.")

        statistics.generated_segments = len(all_segments)

        progress_callback(
            _make_progress(
                started_at=started_at,
                stage="Packing token-limited outputs",
                completed=0,
                total=len(all_segments),
                detail="Calculating final part boundaries",
                token_limit=self._config.token_limit,
            )
        )

        output_token_limit = (
            self._config.token_limit
            if self._config.token_limit is not None
            else DEFAULT_OUTPUT_PART_TOKENS
        )

        if self._config.token_limit is None:
            self._logger.info(
                "Using automatic output token limit=%d",
                output_token_limit,
            )

        packed_parts = pack_segments(
            segments=all_segments,
            token_limit=output_token_limit,
            encoding_name=self._config.encoding_name,
            token_counter=self._token_counter,
            progress_callback=progress_callback,
        )

        progress_callback(
            _make_progress(
                started_at=started_at,
                stage="Writing output parts",
                completed=0,
                total=len(packed_parts),
                detail="Creating atomic output files",
                token_limit=self._config.token_limit,
            )
        )

        output_parts = write_output_parts(
            packed_parts=packed_parts,
            output_directory=self._config.output_directory,
            output_prefix=resolved_output_prefix,
            token_limit=self._config.token_limit,
            encoding_name=self._config.encoding_name,
            token_counter=self._token_counter,
            progress_callback=progress_callback,
        )

        for part in output_parts:
            self._logger.info(
                "Wrote part=%d path=%s tokens=%d characters=%d sha256=%s",
                part.part_number,
                part.path,
                part.token_count,
                part.character_count,
                part.sha256,
            )

        statistics.output_parts = len(output_parts)
        statistics.output_tokens = sum(part.token_count for part in output_parts)

        manifest_path = write_manifest(
            output_directory=self._config.output_directory,
            input_directory=self._config.input_directory,
            output_parts=output_parts,
            statistics=statistics,
            token_limit=self._config.token_limit,
            encoding_name=self._config.encoding_name,
        )

        elapsed_seconds = perf_counter() - started_at

        self._logger.info(
            "Merge completed prefix=%s parts=%d sources=%d "
            "segments=%d output_tokens=%d elapsed_seconds=%.3f "
            "manifest=%s",
            resolved_output_prefix,
            statistics.output_parts,
            statistics.processed_source_files,
            statistics.generated_segments,
            statistics.output_tokens,
            elapsed_seconds,
            manifest_path,
        )

        return MergeResult(
            input_directory=self._config.input_directory,
            output_directory=self._config.output_directory,
            output_parts=tuple(output_parts),
            manifest_path=manifest_path,
            log_path=self._log_path,
            statistics=statistics,
            elapsed_seconds=elapsed_seconds,
            token_limit=self._config.token_limit,
        )
