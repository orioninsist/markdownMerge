from .splitter import Part


def create_summary(
    parts: list[Part],
    token_limit: int,
    input_files: int,
) -> str:
    lines: list[str] = []

    lines.append("Markdown Merge Summary")
    lines.append("=====================")
    lines.append("")
    lines.append(f"Input Files: {input_files}")
    lines.append(f"Created Parts: {len(parts)}")
    lines.append(f"Token Limit: {token_limit}")
    lines.append("")

    for part in parts:
        lines.append(f"Part {part.number:03d}")
        lines.append("-" * 8)
        lines.append(f"Files: {len(part.files)}")
        lines.append(f"Tokens: {part.tokens}")
        lines.append("")

    return "\n".join(lines)
