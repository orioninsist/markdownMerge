from dataclasses import dataclass
from pathlib import Path

from .tokenizer import TokenCounter


@dataclass
class FileChunk:
    path: Path
    source_path: str
    tokens: int


@dataclass
class Part:
    number: int
    files: list[FileChunk]
    tokens: int


def split_files(
    files: list[Path],
    token_limit: int,
    *,
    input_directory: str | None = None,
    reserve_tokens: int = 5000,
    model: str | None = "gpt-4o",
    encoding_name: str | None = None,
) -> list[Part]:
    if token_limit <= 0:
        raise ValueError("token_limit must be greater than zero.")
    if reserve_tokens < 0:
        raise ValueError("reserve_tokens cannot be negative.")
    if reserve_tokens >= token_limit:
        raise ValueError("reserve_tokens must be smaller than token_limit.")

    effective_limit = token_limit - reserve_tokens
    counter = TokenCounter(
        model=model,
        encoding_name=encoding_name,
    )

    root = Path(input_directory).resolve() if input_directory else None
    parts: list[Part] = []
    current_files: list[FileChunk] = []
    current_tokens = 0
    part_number = 1
    total_files = len(files)

    for index, file_path in enumerate(files, start=1):
        print(f"[{index}/{total_files}] processing {file_path.name}")

        resolved_path = file_path.resolve()
        if root is not None:
            try:
                source_path = resolved_path.relative_to(root).as_posix()
            except ValueError as exc:
                raise ValueError(
                    f"Input file is outside input directory: {file_path}"
                ) from exc
        else:
            source_path = file_path.name

        content = file_path.read_text(encoding="utf-8")
        source_header = f"# Source: {source_path}\n\n"
        file_tokens = counter.count(source_header + content + "\n\n")

        if file_tokens > effective_limit:
            raise ValueError(
                f"Source file exceeds the effective token limit: {source_path} "
                f"({file_tokens} tokens > {effective_limit}). "
                "Increase --token-limit, reduce --reserve-tokens, or remove the file."
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
                source_path=source_path,
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
