import re
from pathlib import Path

from .splitter import Part


def _get_source_name(parts: list[Part]) -> str:
    for part in parts:
        for file_chunk in part.files:
            parent_name = file_chunk.path.parent.name
            if parent_name:
                return _clean_name(parent_name)
    return "merged_docs"


def _clean_name(name: str) -> str:
    cleaned = name.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = cleaned.strip("_")
    if not cleaned:
        return "merged_docs"
    return cleaned[:50]


def write_parts(parts: list[Part], output_directory: str) -> list[Path]:
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    source_name = _get_source_name(parts)
    created_files: list[Path] = []

    for part in parts:
        file_path = output_path / f"{source_name}_part_{part.number:03d}.md"

        if file_path.exists():
            file_path.unlink()

        with file_path.open("w", encoding="utf-8") as output:
            for file_chunk in part.files:
                output.write(f"# Source: {file_chunk.path.name}\n\n")
                output.write(file_chunk.content)
                output.write("\n\n")

        file_path.chmod(0o644)

        created_files.append(file_path)

    return created_files
