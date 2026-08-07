"""Rich terminal user interface."""

from __future__ import annotations

from contextlib import AbstractContextManager
from pathlib import Path
from types import TracebackType

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from markdown_merge.models import MergeResult

console = Console()


class MergeProgressUI(AbstractContextManager["MergeProgressUI"]):
    """Live Rich progress display used during merge execution."""

    def __init__(
        self,
        input_directory: Path,
        output_directory: Path,
        token_limit: int,
        encoding_name: str,
    ) -> None:
        self._input_directory = input_directory
        self._output_directory = output_directory
        self._token_limit = token_limit
        self._encoding_name = encoding_name

        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=36),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TextColumn("[dim]{task.fields[detail]}"),
            expand=True,
        )

        self._task_id: TaskID | None = None

        configuration = Table.grid(padding=(0, 2))
        configuration.add_column(style="bold")
        configuration.add_column(overflow="fold")
        configuration.add_row("Input", str(input_directory))
        configuration.add_row("Output", str(output_directory))
        configuration.add_row("Token limit", f"{token_limit:,}")
        configuration.add_row("Encoding", encoding_name)

        self._live = Live(
            Group(
                Panel(
                    configuration,
                    title="[bold]Markdown Merge Configuration",
                    border_style="cyan",
                ),
                Panel(
                    self._progress,
                    title="[bold]Execution",
                    border_style="blue",
                ),
            ),
            console=console,
            refresh_per_second=10,
        )

    def __enter__(self) -> MergeProgressUI:
        """Start the live terminal display."""
        self._live.__enter__()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Stop the live terminal display."""
        self._live.__exit__(
            exception_type,
            exception,
            traceback,
        )

    def update(
        self,
        stage: str,
        completed: int,
        total: int,
        detail: str,
    ) -> None:
        """Create or update the active progress task."""
        safe_total = max(total, 1)

        if self._task_id is None:
            self._task_id = self._progress.add_task(
                stage,
                total=safe_total,
                completed=completed,
                detail=detail,
            )
            return

        current_task = self._progress.tasks[self._task_id]

        if current_task.description != stage:
            self._progress.update(
                self._task_id,
                description=stage,
                total=safe_total,
                completed=completed,
                detail=detail,
            )
            return

        self._progress.update(
            self._task_id,
            total=safe_total,
            completed=completed,
            detail=detail,
        )


def _number(value: int) -> str:
    """Format an integer for terminal display."""
    return f"{value:,}"


def display_result(result: MergeResult) -> None:
    """Display a complete execution summary."""
    statistics = result.statistics

    summary = Table(
        title="Project Statistics",
        show_header=True,
        header_style="bold cyan",
        border_style="cyan",
    )
    summary.add_column("Metric")
    summary.add_column("Value", justify="right")

    summary.add_row(
        "Directories scanned",
        _number(statistics.directories_scanned),
    )
    summary.add_row(
        "Markdown files discovered",
        _number(statistics.discovered_markdown_files),
    )
    summary.add_row(
        "Source files processed",
        _number(statistics.processed_source_files),
    )
    summary.add_row(
        "Skipped files",
        _number(statistics.skipped_files),
    )
    summary.add_row(
        "Failed files",
        _number(statistics.failed_files),
    )
    summary.add_row(
        "Oversized sources split",
        _number(statistics.oversized_sources_split),
    )
    summary.add_row(
        "Generated source segments",
        _number(statistics.generated_segments),
    )
    summary.add_row(
        "Original characters",
        _number(statistics.original_characters),
    )
    summary.add_row(
        "Cleaned characters",
        _number(statistics.cleaned_characters),
    )
    summary.add_row(
        "Removed characters",
        (f"{_number(statistics.removed_characters)} ({statistics.reduction_percentage:.2f}%)"),
    )
    summary.add_row(
        "Source tokens",
        _number(statistics.source_tokens),
    )
    summary.add_row(
        "Final output tokens",
        _number(statistics.output_tokens),
    )
    summary.add_row(
        "Output parts",
        _number(statistics.output_parts),
    )
    summary.add_row(
        "Elapsed time",
        f"{result.elapsed_seconds:.2f} seconds",
    )

    parts = Table(
        title="Generated Output Parts",
        show_header=True,
        header_style="bold green",
        border_style="green",
    )
    parts.add_column("Part", justify="right")
    parts.add_column("Filename")
    parts.add_column("Tokens", justify="right")
    parts.add_column("Capacity", justify="right")
    parts.add_column("Segments", justify="right")
    parts.add_column("SHA-256", overflow="fold")

    for part in result.output_parts:
        capacity = part.token_count / result.token_limit * 100

        parts.add_row(
            str(part.part_number),
            part.filename,
            _number(part.token_count),
            f"{capacity:.2f}%",
            _number(len(part.segments)),
            part.sha256[:16],
        )

    locations = Table.grid(padding=(0, 2))
    locations.add_column(style="bold")
    locations.add_column(overflow="fold")
    locations.add_row(
        "Output directory",
        str(result.output_directory),
    )
    locations.add_row(
        "Manifest",
        str(result.manifest_path),
    )
    locations.add_row(
        "Execution log",
        str(result.log_path),
    )

    console.print()
    console.print(summary)
    console.print()
    console.print(parts)
    console.print()
    console.print(
        Panel(
            locations,
            title="[bold]Generated Artifacts",
            border_style="magenta",
        )
    )

    if statistics.warnings:
        warning_text = Text()

        for warning in statistics.warnings:
            warning_text.append(f"• {warning}\n")

        console.print(
            Panel(
                warning_text,
                title="[bold yellow]Warnings",
                border_style="yellow",
            )
        )

    console.print(
        Panel.fit(
            "[bold green]Merge completed successfully.[/bold green]\n"
            "Every generated Markdown file is within the configured token limit.",
            border_style="green",
        )
    )


def display_failure(
    error: BaseException,
    log_path: Path | None = None,
) -> None:
    """Display a failure message with the log location."""
    details = Text()
    details.append(
        f"{type(error).__name__}: ",
        style="bold red",
    )
    details.append(str(error))

    if log_path is not None:
        details.append(
            "\n\nExecution log: ",
            style="bold",
        )
        details.append(
            str(log_path),
            style="cyan",
        )

    console.print(
        Panel(
            details,
            title="[bold red]Merge Failed",
            border_style="red",
        )
    )
