import re
from pathlib import Path

from .splitter import Part


def _clean_name(name: str) -> str:
    cleaned = name.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = cleaned.strip("_")

    if not cleaned:
        return "merged_docs"

    return cleaned[:50]


def _get_source_name(input_directory: str) -> str:
    input_path = Path(input_directory)
    parts = input_path.parts

    docs_indexes = [index for index, part in enumerate(parts) if part.lower() == "docs"]

    if docs_indexes:
        docs_index = docs_indexes[-1]

        if docs_index + 1 < len(parts):
            return _clean_name(parts[docs_index + 1])

        if docs_index > 0:
            return _clean_name(parts[docs_index - 1])

    if input_path.name:
        return _clean_name(input_path.name)

    return "merged_docs"


def write_parts(
    parts: list[Part],
    output_directory: str,
    input_directory: str,
) -> list[Path]:
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    source_name = _get_source_name(input_directory)
    created_files: list[Path] = []

    for part in parts:
        file_path = output_path / f"{source_name}-{part.number}.md"

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
