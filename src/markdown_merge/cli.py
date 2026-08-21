"""Command-line interface."""

from __future__ import annotations

import logging
from pathlib import Path

import click

from markdown_merge.config import MergeConfig
from markdown_merge.logging_setup import configure_logging
from markdown_merge.models import ProgressUpdate
from markdown_merge.service import MarkdownMergeService
from markdown_merge.ui import (
    display_failure,
    display_result,
)


def terminal_progress(update: ProgressUpdate) -> None:
    """Print stable terminal progress lines."""
    parts = [
        update.stage,
        f"{update.completed}/{update.total}",
    ]

    if update.current_source:
        parts.append(update.current_source)

    if update.current_part is not None:
        parts.append(f"part={update.current_part}")

    if update.current_tokens is not None:
        parts.append(f"tokens={update.current_tokens:,}")

    if update.detail:
        parts.append(update.detail)

    print(" | ".join(parts), flush=True)


def _project_root() -> Path:
    """Resolve the installed project root when possible."""
    source_file = Path(__file__).resolve()
    candidate = source_file.parents[2]

    if (candidate / "pyproject.toml").exists():
        return candidate

    return Path.cwd()


@click.command(
    context_settings={
        "help_option_names": ["-h", "--help"],
        "show_default": True,
    },
    epilog="""Examples:

  mdmerge ./docs ./output

  mdmerge ./docs ./output --token-limit 250000
""",
)
@click.argument(
    "input_directory",
    type=click.Path(
        path_type=Path,
        exists=True,
        file_okay=False,
        dir_okay=True,
        readable=True,
        resolve_path=True,
    ),
)
@click.argument(
    "output_directory",
    type=click.Path(
        path_type=Path,
        file_okay=False,
        dir_okay=True,
        writable=True,
        resolve_path=True,
    ),
)
@click.option(
    "--token-limit",
    type=click.IntRange(min=1_000),
    default=80_000,
    help="Maximum token count allowed for each generated Markdown file.",
)
@click.option(
    "--encoding",
    "encoding_name",
    default="o200k_base",
    help="tiktoken encoding used for exact token counting. Usually does not need to be changed.",
)
@click.option(
    "--output-prefix",
    default=None,
    help=(
        "Filename prefix for generated files. When omitted, a prefix is "
        "derived automatically from Markdown headings and content."
    ),
)
@click.option(
    "--toc-reserve",
    type=click.IntRange(min=100),
    default=2_000,
    help="Tokens reserved for generated headings and table-of-contents metadata.",
)
@click.version_option(package_name="markdown-merge")
def main(
    input_directory: Path,
    output_directory: Path,
    token_limit: int,
    encoding_name: str,
    output_prefix: str | None,
    toc_reserve: int,
) -> None:
    """Recursively clean, merge, and intelligently split Markdown documents."""
    project_root = _project_root()
    logger: logging.Logger | None = None
    log_path: Path | None = None

    try:
        logger, log_path = configure_logging(project_root / "logs")

        config = MergeConfig(
            input_directory=input_directory,
            output_directory=output_directory,
            project_root=project_root,
            token_limit=token_limit,
            encoding_name=encoding_name,
            output_prefix=output_prefix,
            toc_reserve_tokens=toc_reserve,
        )

        service = MarkdownMergeService(
            config=config,
            logger=logger,
            log_path=log_path,
        )

        result = service.execute(progress_callback=terminal_progress)

        display_result(result)

    except (OSError, RuntimeError, ValueError) as error:
        if logger is not None:
            logger.exception("Merge execution failed")

        display_failure(error, log_path)
        raise click.exceptions.Exit(1) from error

    except KeyboardInterrupt as error:
        if logger is not None:
            logger.warning("Merge interrupted by user")

        display_failure(
            RuntimeError("Execution interrupted by user."),
            log_path,
        )
        raise click.exceptions.Exit(130) from error


if __name__ == "__main__":
    main()
