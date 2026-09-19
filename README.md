# markdownMerge

A token-aware Markdown packer designed to combine large Markdown documentation sets into upload-friendly parts while keeping every source file intact.

It is useful for LLM workflows where both file count and token budgets matter. markdownMerge recursively scans Markdown files, measures them with tiktoken, preserves file boundaries, writes deterministic parts, re-validates the final output, and produces machine-readable metadata.

## Features

| Feature | Description |
|---|---|
| Markdown Scanner | Recursively finds all .md files from an input directory |
| File Preservation | Source Markdown files are never modified or split |
| Relative Source Tracking | Adds the source path relative to the input root |
| Token Counting | Uses selectable tiktoken model or encoding |
| Token Reserve | Keeps a configurable safety budget unused in each part |
| Oversized File Guard | Fails clearly when one source file cannot fit |
| Low-Memory Writing | Stores metadata in memory and re-reads content while writing |
| Final Validation | Re-tokenizes written output and enforces the requested limit |
| Summary Report | Reports final token counts for generated parts |
| JSON Manifest | Records token settings, part metadata, and source membership |

## Usage

```bash
mdmerge INPUT_DIRECTORY OUTPUT_DIRECTORY \
  --token-limit 120000 \
  --reserve-tokens 5000 \
  --model gpt-4o
```

Or choose an explicit encoding:

```bash
mdmerge INPUT_DIRECTORY OUTPUT_DIRECTORY \
  --token-limit 120000 \
  --reserve-tokens 5000 \
  --encoding o200k_base
```

--model and --encoding are mutually exclusive.

The effective planning budget is:

```text
token-limit - reserve-tokens
```

The final written Markdown files are re-tokenized and must remain below --token-limit.

## Output

```text
output/
├── docs-1.md
├── docs-2.md
├── manifest.json
├── summary.txt
└── validation.txt
```

Each merged section keeps its input-relative path:

```markdown
# Source: introduction.md

(original content)

# Source: guides/setup.md

(original content)
```

If a complete source file is larger than the effective token budget, markdownMerge exits with an error instead of splitting that source file.

## Development

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
./quality.sh
```

## Design Principles

- Never modify or split source Markdown files.
- Preserve deterministic input ordering.
- Fail loudly for impossible token budgets.
- Track sources with relative paths.
- Avoid retaining every file body in memory.
- Re-tokenize the written output before reporting success.
- Keep platform-specific upload limits separate from tokenizer counts.

## Scope

This project manages Markdown packing and tokenizer budgets. Token counts are not identical to every upload, retrieval, file-size, or context rule an LLM product may impose. Those platform-specific limits should be checked separately.

## License

MIT License
