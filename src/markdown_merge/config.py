"""Application configuration."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MergeConfig:
    """Configuration for a Markdown merge execution."""

    input_directory: Path
    output_directory: Path
    project_root: Path
    token_limit: int | None = None
    encoding_name: str = "o200k_base"
    output_prefix: str | None = None
    minimum_split_search_tokens: int = 512
    toc_reserve_tokens: int = 2_000

    @property
    def logs_directory(self) -> Path:
        """Return the directory used for execution logs."""
        return self.project_root / "logs"

    def validate(self) -> None:
        """Validate runtime configuration."""
        if not self.input_directory.exists():
            raise FileNotFoundError(f"Input directory does not exist: {self.input_directory}")

        if not self.input_directory.is_dir():
            raise NotADirectoryError(f"Input path is not a directory: {self.input_directory}")

        if self.token_limit is not None and self.token_limit < 1_000:
            raise ValueError("Token limit must be at least 1,000.")

        if self.toc_reserve_tokens < 100:
            raise ValueError("TOC reserve must be at least 100 tokens.")

        if self.token_limit is not None and self.toc_reserve_tokens >= self.token_limit:
            raise ValueError("TOC reserve must be lower than the token limit.")

        if self.input_directory.resolve() == self.output_directory.resolve():
            raise ValueError("Input and output directories must be different.")
