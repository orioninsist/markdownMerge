# markdownMerge

A token-aware Markdown merge tool designed to combine thousands of Markdown files into optimized output parts without modifying the original Markdown content.

The project is built for large documentation datasets such as OpenAI documentation exports. It keeps every source file complete, calculates exact token usage with `tiktoken`, and splits the final merged output according to a user-defined token limit.

---

# Features

| Feature | Description |
|---|---|
| Markdown Scanner | Recursively finds all `.md` files from an input directory |
| File Preservation | Original Markdown content is kept unchanged |
| Source Tracking | Adds a source marker before every merged file |
| Token Counting | Uses `tiktoken` for accurate token calculation |
| Smart Splitting | Splits output only between files, never inside a file |
| Token Safety | Keeps generated parts below the requested token limit |
| Validation | Checks every generated part after writing |
| Summary Report | Creates a complete merge summary |

---

# Architecture

```

Markdown Files
|
v
+-------------+
|  scanner.py |
+-------------+
|
v
+---------------+
| tokenizer.py  |
+---------------+
|
v
+---------------+
| splitter.py   |
+---------------+
|
v
+-------------+
| writer.py   |
+-------------+
|
v
+--------------+
| validator.py |
+--------------+
|
v
Merged Markdown Parts

````

---

# Installation

Clone the repository:

```bash
git clone <repository-url>
cd markdownMerge
````

Install dependencies:

```bash
uv sync
```

Install the command line tool:

```bash
uv tool install --editable .
```

Verify installation:

```bash
mdmerge --help
```

---

# Basic Usage

```bash
mdmerge INPUT_DIRECTORY OUTPUT_DIRECTORY --token-limit TOKEN_LIMIT
```

Example:

```bash
mdmerge ./docs ./merged --token-limit 1500000
```

This command:

1. Finds all Markdown files inside `./docs`
2. Counts tokens for every file
3. Groups files into parts
4. Writes merged Markdown files into `./merged`
5. Generates summary and validation reports

---

# Command Parameters

| Parameter          | Required | Description                                         |
| ------------------ | -------- | --------------------------------------------------- |
| `INPUT_DIRECTORY`  | Yes      | Folder containing Markdown files                    |
| `OUTPUT_DIRECTORY` | Yes      | Folder where generated parts are saved              |
| `--token-limit`    | Yes      | Maximum token capacity allowed for each output part |

---

# Example Workflow

Input:

```
docs/
├── introduction.md
├── api.md
├── examples.md
└── guides/
    └── setup.md
```

Command:

```bash
mdmerge docs output --token-limit 100000
```

Output:

```
output/
├── part_001.md
├── part_002.md
├── summary.txt
└── validation.txt
```

---

# Output Format

Every merged file keeps source information:

```markdown
# Source: introduction.md

(original markdown content)

# Source: api.md

(original markdown content)
```

The original files are never deleted or modified.

---

# Summary Report

Example:

```
Markdown Merge Summary

Input Files: 21969
Created Parts: 34
Token Limit: 1500000

Part 001
Files: 542
Tokens: 723770

Part 002
Files: 66
Tokens: 1483156
```

---

# Validation Report

After generation, every part is checked.

Example:

```
part_001.md

Tokens: 723228
Sources: 542
Status: OK


Validation Result: PASSED
```

Validation guarantees:

| Check                      | Result |
| -------------------------- | ------ |
| Token limit respected      | Yes    |
| Source markers exist       | Yes    |
| Output files readable      | Yes    |
| Markdown content preserved | Yes    |

---

# Development Commands

Run formatting check:

```bash
uv run ruff format --check .
```

Run linting:

```bash
uv run ruff check .
```

Run type checking:

```bash
uv run mypy
```

Run tests:

```bash
uv run pytest
```

Run complete quality pipeline:

```bash
./quality.sh
```

---

# Design Principles

| Principle               | Meaning                                       |
| ----------------------- | --------------------------------------------- |
| No Content Modification | Markdown files are merged exactly as provided |
| File Boundary Splitting | A file is never cut into pieces               |
| Exact Token Accounting  | Token limits are measured with `tiktoken`     |
| Simple Pipeline         | Small modules with clear responsibilities     |
| Reproducible Output     | Same input produces predictable results       |

---

# Project Status

Current capabilities:

| Component            | Status   |
| -------------------- | -------- |
| Markdown scanning    | Complete |
| Token counting       | Complete |
| File-based splitting | Complete |
| Output writing       | Complete |
| Validation           | Complete |
| Automated tests      | Complete |

---

# License

MIT License
