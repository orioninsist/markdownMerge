from pathlib import Path

from .splitter import Part


def write_parts(parts: list[Part], output_directory: str) -> list[Path]:
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)

    created_files: list[Path] = []

    for part in parts:
        file_path = output_path / f"part_{part.number:03d}.md"

        with file_path.open("w", encoding="utf-8") as output:
            for file_chunk in part.files:
                output.write(
                    f"# Source: {file_chunk.path.name}\n\n"
                )
                output.write(file_chunk.content)
                output.write("\n\n")

        created_files.append(file_path)

    return created_files
