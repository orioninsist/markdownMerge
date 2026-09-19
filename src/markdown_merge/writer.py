from pathlib import Path

from .naming import unique_part_filenames
from .splitter import Part


def write_parts(
    parts: list[Part],
    output_directory: str,
    input_directory: str,
) -> list[Path]:
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    created_files: list[Path] = []
    filenames = unique_part_filenames(parts, input_directory=input_directory)

    for part, filename in zip(parts, filenames, strict=True):
        file_path = output_path / filename

        with file_path.open("w", encoding="utf-8") as output:
            for file_chunk in part.files:
                output.write(f"# Source: {file_chunk.source_path}\n\n")
                output.write(file_chunk.path.read_text(encoding="utf-8"))
                output.write("\n\n")

        file_path.chmod(0o644)
        created_files.append(file_path)

    return created_files
