import argparse
from pathlib import Path

from .scanner import scan_markdown_files
from .splitter import split_files
from .summary import create_summary
from .validator import validate_output
from .writer import write_parts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge Markdown files by token limit without modifying content."
    )

    parser.add_argument("input_directory")
    parser.add_argument("output_directory")
    parser.add_argument(
        "--token-limit",
        type=int,
        required=True,
    )

    args = parser.parse_args()

    print("Markdown Merge Started")
    print()
    print(f"Input: {args.input_directory}")
    print(f"Output: {args.output_directory}")
    print(f"Token Limit: {args.token_limit}")
    print()

    print("Scanning markdown files...")
    files = scan_markdown_files(args.input_directory)

    if not files:
        raise SystemExit("No Markdown files found.")

    print(f"Found files: {len(files)}")
    print()

    print("Counting tokens and creating parts...")
    parts = split_files(
        files,
        args.token_limit,
    )

    print(f"Created parts: {len(parts)}")
    print()

    print("Writing output files...")
    write_parts(
        parts,
        args.output_directory,
    )

    summary = create_summary(
        parts,
        args.token_limit,
        len(files),
    )

    output_path = Path(args.output_directory)

    summary_path = output_path / "summary.txt"

    if summary_path.exists():
        summary_path.unlink()

    summary_path.write_text(
        summary,
        encoding="utf-8",
    )

    summary_path.chmod(0o644)

    validation = validate_output(
        args.output_directory,
        args.token_limit,
    )

    validation_path = output_path / "validation.txt"

    if validation_path.exists():
        validation_path.unlink()

    validation_path.write_text(
        validation,
        encoding="utf-8",
    )

    validation_path.chmod(0o644)

    print()
    print(summary)
    print()
    print(validation)
    print()
    print("Completed.")
