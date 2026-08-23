"""Domain models used by the Markdown merger."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourceDocument:
    """A cleaned Markdown source document."""

    absolute_path: Path
    relative_path: Path
    content: str
    original_characters: int
    cleaned_characters: int
    content_tokens: int


@dataclass(frozen=True, slots=True)
class DocumentSegment:
    """A complete or partial source document ready for packing."""

    source_path: Path
    segment_index: int
    segment_count: int
    content: str
    rendered_content: str
    token_count: int

    @property
    def display_name(self) -> str:
        """Return the source name displayed in the TOC and source header."""
        if self.segment_count == 1:
            return self.source_path.as_posix()
        return f"{self.source_path.as_posix()} (segment {self.segment_index}/{self.segment_count})"


@dataclass(frozen=True, slots=True)
class OutputPart:
    """One merged Markdown output part."""

    part_number: int
    filename: str
    path: Path
    token_count: int
    character_count: int
    segments: tuple[DocumentSegment, ...]
    sha256: str


@dataclass(slots=True)
class MergeStatistics:
    """Mutable statistics collected throughout one merge run."""

    directories_scanned: int = 0
    discovered_markdown_files: int = 0
    processed_source_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    original_characters: int = 0
    cleaned_characters: int = 0
    source_tokens: int = 0
    output_tokens: int = 0
    output_parts: int = 0
    oversized_sources_split: int = 0
    generated_segments: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def removed_characters(self) -> int:
        """Return the number of characters removed by cleaning."""
        return max(0, self.original_characters - self.cleaned_characters)

    @property
    def reduction_percentage(self) -> float:
        """Return the cleaning reduction percentage."""
        if self.original_characters == 0:
            return 0.0
        return self.removed_characters / self.original_characters * 100


@dataclass(frozen=True, slots=True)
class MergeResult:
    """Final result returned by the merge service."""

    input_directory: Path
    output_directory: Path
    output_parts: tuple[OutputPart, ...]
    manifest_path: Path
    log_path: Path
    statistics: MergeStatistics
    elapsed_seconds: float
    token_limit: int | None


@dataclass(frozen=True, slots=True)
class ProgressUpdate:
    """Structured real-time progress information."""

    stage: str
    completed: int
    total: int
    detail: str = ""
    current_source: str | None = None
    current_part: int | None = None
    current_tokens: int | None = None
    token_limit: int | None = None
    elapsed_seconds: float | None = None
    items_per_second: float | None = None
    eta_seconds: float | None = None
