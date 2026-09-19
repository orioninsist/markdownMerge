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


def _source_path(file_path: Path, root: Path | None) -> str:
    resolved_path = file_path.resolve()
    if root is None:
        return file_path.name

    try:
        return resolved_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"Input file is outside input directory: {file_path}"
        ) from exc


def _measure_files(
    files: list[Path],
    *,
    root: Path | None,
    counter: TokenCounter,
    effective_limit: int,
) -> list[FileChunk]:
    chunks: list[FileChunk] = []
    total_files = len(files)

    for index, file_path in enumerate(files, start=1):
        print(f"[{index}/{total_files}] processing {file_path.name}")

        source_path = _source_path(file_path, root)
        content = file_path.read_text(encoding="utf-8")
        source_header = f"# Source: {source_path}\n\n"
        file_tokens = counter.count(source_header + content + "\n\n")

        if file_tokens > effective_limit:
            raise ValueError(
                f"Source file exceeds the effective token limit: {source_path} "
                f"({file_tokens} tokens > {effective_limit}). "
                "Increase --token-limit, reduce --reserve-tokens, or remove the file."
            )

        chunks.append(
            FileChunk(
                path=file_path,
                source_path=source_path,
                tokens=file_tokens,
            )
        )

    return chunks


def _pack_first_fit_decreasing(
    chunks: list[FileChunk],
    *,
    effective_limit: int,
) -> list[Part]:
    ordered = sorted(
        chunks,
        key=lambda chunk: (-chunk.tokens, chunk.source_path),
    )
    parts: list[Part] = []

    for chunk in ordered:
        for part in parts:
            if part.tokens + chunk.tokens <= effective_limit:
                part.files.append(chunk)
                part.tokens += chunk.tokens
                break
        else:
            parts.append(
                Part(
                    number=len(parts) + 1,
                    files=[chunk],
                    tokens=chunk.tokens,
                )
            )

    return parts


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

    chunks = _measure_files(
        files,
        root=root,
        counter=counter,
        effective_limit=effective_limit,
    )
    return _pack_first_fit_decreasing(
        chunks,
        effective_limit=effective_limit,
    )
