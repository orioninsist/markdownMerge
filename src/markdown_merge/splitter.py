from dataclasses import dataclass
from pathlib import Path

from .tokenizer import count_tokens


@dataclass
class FileChunk:
    path: Path
    content: str
    tokens: int


@dataclass
class Part:
    number: int
    files: list[FileChunk]
    tokens: int


def split_files(
    files: list[Path],
    token_limit: int,
) -> list[Part]:
    parts: list[Part] = []

    effective_limit = token_limit - 5000

    current_files: list[FileChunk] = []
    current_tokens = 0
    part_number = 1

    total_files = len(files)

    for index, file_path in enumerate(files, start=1):
        print(f"[{index}/{total_files}] processing {file_path.name}")

        content = file_path.read_text(encoding="utf-8")

        source_header = f"# Source: {file_path.name}\n\n"

        file_tokens = (
            count_tokens(source_header) + count_tokens(content) + count_tokens("\n\n")
        )

        if current_files and current_tokens + file_tokens > effective_limit:
            parts.append(
                Part(
                    number=part_number,
                    files=current_files,
                    tokens=current_tokens,
                )
            )

            part_number += 1
            current_files = []
            current_tokens = 0

        current_files.append(
            FileChunk(
                path=file_path,
                content=content,
                tokens=file_tokens,
            )
        )

        current_tokens += file_tokens

    if current_files:
        parts.append(
            Part(
                number=part_number,
                files=current_files,
                tokens=current_tokens,
            )
        )

    return parts
