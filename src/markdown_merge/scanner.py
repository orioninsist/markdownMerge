from pathlib import Path


def scan_markdown_files(input_directory: str) -> list[Path]:
    path = Path(input_directory)

    if not path.exists():
        raise FileNotFoundError(f"Input directory not found: {input_directory}")

    return sorted(
        file
        for file in path.rglob("*.md")
        if file.is_file()
    )
