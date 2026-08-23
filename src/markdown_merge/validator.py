from pathlib import Path

from .tokenizer import count_tokens


def validate_output(
    output_directory: str,
    token_limit: int,
) -> str:
    output_path = Path(output_directory)

    parts = sorted(output_path.glob("part_*.md"))

    lines: list[str] = []

    lines.append("Markdown Merge Validation")
    lines.append("========================")
    lines.append("")

    lines.append(f"Parts Found: {len(parts)}")
    lines.append("")

    failed = False

    for part in parts:
        content = part.read_text(encoding="utf-8")
        tokens = count_tokens(content)
        sources = content.count("# Source:")

        status = "OK"

        if tokens > token_limit:
            status = "FAILED"
            failed = True

        lines.append(part.name)
        lines.append(f"  Tokens: {tokens}")
        lines.append(f"  Sources: {sources}")
        lines.append(f"  Status: {status}")
        lines.append("")

    if failed:
        lines.append("Validation Result: FAILED")
    else:
        lines.append("Validation Result: PASSED")

    return "\n".join(lines)
