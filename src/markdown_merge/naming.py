import re
from collections import Counter
from pathlib import Path

from .splitter import Part

_GENERIC_STEMS = {
    "index",
    "readme",
    "overview",
    "introduction",
    "intro",
    "home",
    "main",
    "getting_started",
    "getting-started",
    "guide",
    "guides",
    "docs",
    "documentation",
    "reference",
}

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "api",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def _slug(value: str, *, max_length: int = 64) -> str:
    value = value.lower().replace("_", "-")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:max_length].rstrip("-")


def _tokens(value: str) -> list[str]:
    normalized = _slug(value, max_length=200)
    return [
        token
        for token in normalized.split("-")
        if len(token) > 1 and token not in _STOP_WORDS
    ]


def _meaningful_stem(path: Path) -> str | None:
    stem = _slug(path.stem, max_length=80)
    if not stem or stem in _GENERIC_STEMS:
        return None
    return stem


def _fallback_source_name(input_directory: str) -> str:
    input_path = Path(input_directory)
    parts = input_path.parts

    docs_indexes = [index for index, part in enumerate(parts) if part.lower() == "docs"]
    if docs_indexes:
        docs_index = docs_indexes[-1]
        if docs_index + 1 < len(parts):
            candidate = _slug(parts[docs_index + 1])
            if candidate:
                return candidate
        if docs_index > 0:
            candidate = _slug(parts[docs_index - 1])
            if candidate:
                return candidate

    candidate = _slug(input_path.name)
    return candidate or "merged-docs"


def _common_directory(parts: list[Path]) -> str | None:
    if not parts:
        return None

    first_components = [path.parts[0] for path in parts if len(path.parts) > 1]
    if len(first_components) != len(parts):
        return None

    if len(set(first_components)) == 1:
        candidate = _slug(first_components[0])
        if candidate and candidate not in _GENERIC_STEMS:
            return candidate
    return None


def semantic_part_name(
    part: Part,
    *,
    input_directory: str,
    max_topics: int = 3,
) -> str:
    source_paths = [Path(chunk.source_path) for chunk in part.files]
    fallback = _fallback_source_name(input_directory)

    common_dir = _common_directory(source_paths)
    stems = [
        stem
        for path in source_paths
        if (stem := _meaningful_stem(path)) is not None
    ]

    token_counts: Counter[str] = Counter()
    first_seen: dict[str, int] = {}
    for index, path in enumerate(source_paths):
        components = list(path.parts[:-1])
        stem = _meaningful_stem(path)
        if stem:
            components.append(stem)

        for component in components:
            for token in _tokens(component):
                token_counts[token] += 1
                first_seen.setdefault(token, index)

    ranked_tokens = sorted(
        token_counts,
        key=lambda token: (-token_counts[token], first_seen[token], token),
    )

    topics: list[str] = []
    if common_dir:
        topics.append(common_dir)

    for stem in stems:
        if stem not in topics:
            topics.append(stem)
        if len(topics) >= max_topics:
            break

    if len(topics) < max_topics:
        for token in ranked_tokens:
            if token not in topics:
                topics.append(token)
            if len(topics) >= max_topics:
                break

    if not topics:
        topics = [fallback]

    base = _slug("-".join(topics), max_length=64)
    return base or fallback


def unique_part_filenames(
    parts: list[Part],
    *,
    input_directory: str,
) -> list[str]:
    used: Counter[str] = Counter()
    names: list[str] = []

    for part in parts:
        base = semantic_part_name(part, input_directory=input_directory)
        used[base] += 1
        suffix = "" if used[base] == 1 else f"-{used[base]}"
        names.append(f"{base}{suffix}.md")

    return names
