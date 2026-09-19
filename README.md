# markdownMerge

A token-aware Markdown packer for large documentation collections and LLM upload workflows.

markdownMerge recursively scans Markdown files, counts tokens with OpenAI's `tiktoken`, packs complete source files into deterministic output parts with First-Fit Decreasing, writes the merged Markdown files, and then re-tokenizes the final outputs for validation.

Source Markdown files are never split and their content is never rewritten.

## Purpose

Use markdownMerge when you have many Markdown files and want to reduce them to fewer upload-ready files without exceeding a token budget.

Typical workflow:

```text
many Markdown files
        |
        v
recursive scan
        |
        v
tiktoken measurement
        |
        v
First-Fit Decreasing packing
        |
        v
fewer merged Markdown files
        |
        v
final token validation
        |
        +--> summary.txt
        +--> validation.txt
        +--> manifest.json
```

The project focuses on one job:

- keep each source file intact
- keep source content unchanged
- respect a configured token budget
- minimize the number of merged output files
- keep output deterministic
- preserve source traceability
- validate the actual files written to disk

## Architecture

```text
Input directory
      |
      v
scanner.py
      |
      v
tokenizer.py
      |
      v
splitter.py
      |
      v
writer.py
      |
      v
validator.py
      |
      +--> summary.txt
      +--> validation.txt
      +--> manifest.json
      |
      v
Merged Markdown parts
```

### scanner.py

Recursively discovers `.md` files in deterministic sorted order.

The input path must be a directory.

The CLI rejects an output directory that is equal to, or located inside, the input directory. This prevents generated files from being picked up as source files on later runs.

### tokenizer.py

Uses the `tiktoken` Python package.

Tokenization is delegated to tiktoken's native implementation; markdownMerge itself remains a Python application.

Two tokenizer selection modes are available:

```text
--model MODEL
--encoding ENCODING
```

They are mutually exclusive.

Examples:

```bash
--model gpt-4o
```

```bash
--encoding o200k_base
```

### splitter.py

Measures every complete source file together with its generated source marker:

```markdown
# Source: guides/setup.md
```

The usable planning budget is:

```text
effective limit = token limit - reserve tokens
```

Sources are sorted by:

1. token count, descending
2. source path, ascending, as a deterministic tie-breaker

They are then packed with First-Fit Decreasing.

This generally produces fewer output files than sequential packing.

If one source file is larger than the effective token limit, markdownMerge stops with an error. It does not split that source file.

### writer.py

Writes every planned part to disk.

Each merged section starts with a source marker:

```markdown
# Source: api/authentication.md

(original source content)
```

The original Markdown body is not rewritten, summarized, normalized, or otherwise transformed.

### validator.py

Re-reads and re-tokenizes the final generated Markdown files.

Validation fails when:

- no output parts were generated
- an output part has no source marker
- a final output part exceeds `--token-limit`

The final written file is authoritative, not only the planning estimate.

### summary.txt

Human-readable run summary with part and token statistics.

### validation.txt

Human-readable validation report for each generated part.

### manifest.json

Machine-readable metadata including:

- input directory
- token limit
- reserve tokens
- effective token limit
- tokenizer selection
- input file count
- created part count
- validation result
- final token count for each part
- source files contained in each part

## Requirements

- Python 3.11 or newer
- `uv`
- supported platform for the installed `tiktoken` package

You do not need to clone or build the tiktoken repository separately.

`uv sync` installs the published dependency, normally using a prebuilt wheel when one is available for the current platform.

## Installation

Clone:

```bash
git clone https://github.com/orioninsist/markdownMerge.git
cd markdownMerge
```

Install runtime dependencies:

```bash
uv sync
```

Install runtime plus development dependencies:

```bash
uv sync --group dev
```

Check the CLI:

```bash
uv run mdmerge --help
```

## Command syntax

```bash
uv run mdmerge INPUT_DIRECTORY OUTPUT_DIRECTORY \
  --token-limit TOKEN_LIMIT \
  [--reserve-tokens RESERVE_TOKENS] \
  [--model MODEL | --encoding ENCODING]
```

Required arguments:

```text
INPUT_DIRECTORY
OUTPUT_DIRECTORY
--token-limit
```

Optional arguments:

```text
--reserve-tokens
--model
--encoding
```

Defaults:

```text
--reserve-tokens 5000
--model gpt-4o
```

Because `--model` and `--encoding` are mutually exclusive, use only one of them.

## Recommended usage

For a stable explicit tokenizer selection:

```bash
uv run mdmerge INPUT_DIRECTORY OUTPUT_DIRECTORY \
  --token-limit 120000 \
  --reserve-tokens 5000 \
  --encoding o200k_base
```

Example:

```bash
uv run mdmerge \
  /mnt/local/resources/google/docs \
  /mnt/local/resources/google/merged \
  --token-limit 120000 \
  --reserve-tokens 5000 \
  --encoding o200k_base
```

Planning budget:

```text
token limit:      120000
reserve tokens:     5000
effective limit:  115000
```

The packer plans against 115,000 tokens. The final written file may use the remaining reserve but must not exceed 120,000 tokens.

## All usage variations

### 1. Explicit encoding

Use this when you want to pin the exact tiktoken encoding explicitly.

```bash
uv run mdmerge INPUT OUTPUT \
  --token-limit 120000 \
  --reserve-tokens 5000 \
  --encoding o200k_base
```

### 2. Model-based tokenizer selection

Use this when you want tiktoken to resolve the encoding from a supported model name.

```bash
uv run mdmerge INPUT OUTPUT \
  --token-limit 120000 \
  --reserve-tokens 5000 \
  --model gpt-4o
```

### 3. Use the default model

If neither `--model` nor `--encoding` is supplied, the current CLI default is `gpt-4o`.

```bash
uv run mdmerge INPUT OUTPUT \
  --token-limit 120000
```

Equivalent to:

```bash
uv run mdmerge INPUT OUTPUT \
  --token-limit 120000 \
  --reserve-tokens 5000 \
  --model gpt-4o
```

### 4. No reserve

Useful when you deliberately want the planning budget to equal the final token limit.

```bash
uv run mdmerge INPUT OUTPUT \
  --token-limit 120000 \
  --reserve-tokens 0 \
  --encoding o200k_base
```

This removes the planning safety buffer.

Final validation still runs.

### 5. Larger reserve

Use a larger reserve when you want more unused capacity per generated part.

```bash
uv run mdmerge INPUT OUTPUT \
  --token-limit 120000 \
  --reserve-tokens 10000 \
  --encoding o200k_base
```

Effective packing budget:

```text
110000
```

### 6. Smaller token limit

```bash
uv run mdmerge INPUT OUTPUT \
  --token-limit 50000 \
  --reserve-tokens 5000 \
  --encoding o200k_base
```

Effective packing budget:

```text
45000
```

### 7. Very large corpus

No special command is required for thousands of source files.

```bash
uv run mdmerge \
  /data/docs \
  /data/merged-docs \
  --token-limit 120000 \
  --reserve-tokens 5000 \
  --encoding o200k_base
```

The scanner searches recursively, so nested directories are included automatically.

## Input examples

Simple:

```text
docs/
├── introduction.md
├── api.md
└── setup.md
```

Nested:

```text
docs/
├── api/
│   ├── authentication.md
│   └── errors.md
├── guides/
│   ├── linux.md
│   └── windows.md
└── index.md
```

All nested `.md` files are discovered.

## Output example

If the input directory is:

```text
/docs
```

the generated part names are derived deterministically from the source paths contained in each part:

```text
merged/
├── authentication-tokens.md
├── deployment-linux.md
├── billing-subscriptions.md
├── manifest.json
├── summary.txt
└── validation.txt
```

Naming uses source file stems and useful directory names. Generic names such as `index.md`, `readme.md`, and `overview.md` are de-emphasized. If two parts resolve to the same semantic name, deterministic numeric suffixes such as `-2` are added.

No remote model or API is called for naming; filenames remain local, deterministic, reproducible, and zero-cost.

A merged file looks like:

```markdown
# Source: api/authentication.md

# Authentication

Original content...

# Source: guides/linux.md

# Linux

Original content...
```

## Output directory rule

The output directory must be outside the input directory.

Valid:

```text
input:  /data/docs
output: /data/merged
```

Invalid:

```text
input:  /data/docs
output: /data/docs/merged
```

Also invalid:

```text
input:  /data/docs
output: /data/docs
```

This protection prevents generated merged files from later becoming input sources.

## Token limit rules

`--token-limit` must be greater than zero.

Valid:

```bash
--token-limit 120000
```

Invalid:

```bash
--token-limit 0
```

`--reserve-tokens` cannot be negative.

Valid:

```bash
--reserve-tokens 5000
```

Invalid:

```bash
--reserve-tokens -1
```

Reserve must be smaller than the token limit.

Valid:

```text
token limit:     120000
reserve tokens:   5000
```

Invalid:

```text
token limit:     120000
reserve tokens: 120000
```

## Oversized source files

A single source Markdown file is never divided between parts.

For example:

```text
effective limit: 115000
one-source.md:   130000 tokens
```

markdownMerge exits with an error.

To proceed, you must explicitly choose a larger token limit, a smaller reserve, or change/remove that source file yourself.

markdownMerge will not silently modify it.

## Deterministic packing

The same:

- source contents
- source paths
- token limit
- reserve
- tokenizer

produce the same packing order and output membership.

The packer uses First-Fit Decreasing:

```text
measure all sources
        |
        v
sort largest -> smallest
        |
        v
put each source into the first existing part where it fits
        |
        +-- no existing part fits --> create a new part
```

The goal is fewer output files while remaining below the effective planning limit.

First-Fit Decreasing is a packing heuristic; it is not a guarantee of the mathematically optimal minimum number of bins for every possible input.

## Source integrity

markdownMerge does not:

- rewrite prose
- summarize content
- remove sections
- normalize Markdown
- alter code blocks
- alter syntax-highlight language identifiers
- split a source Markdown file
- semantically cluster or reorder text inside a source file

It only decides which complete source files belong in each merged output part.

Generated source headers are added so each original file remains traceable.

## tiktoken runtime

markdownMerge is written in Python.

Tokenization uses the `tiktoken` dependency.

Conceptually:

```text
markdownMerge
    |
    +-- Python CLI
    +-- Python filesystem logic
    +-- Python packing logic
    +-- Python reporting
    |
    +--> tiktoken Python API
             |
             v
        native tokenization implementation
```

You normally do not build tiktoken manually.

Install everything with:

```bash
uv sync
```

## Choosing model vs encoding

Use:

```bash
--model gpt-4o
```

when you specifically want model-name resolution.

Use:

```bash
--encoding o200k_base
```

when you want to explicitly pin the tokenizer encoding.

For repeatable document packing where model aliases may change over time, explicitly selecting an encoding can make the configuration easier to understand and reproduce.

## What happens during a run

Example command:

```bash
uv run mdmerge docs merged \
  --token-limit 120000 \
  --reserve-tokens 5000 \
  --encoding o200k_base
```

Execution:

```text
1. validate CLI arguments
2. recursively scan docs/
3. count every source with tiktoken
4. reject any individual source above the effective limit
5. sort measured sources by descending token count
6. pack with First-Fit Decreasing
7. write merged Markdown parts
8. re-read every generated part
9. re-tokenize every generated part
10. generate validation.txt
11. generate summary.txt
12. generate manifest.json
13. exit successfully only if validation passes
```

## Checking results

After a successful run:

```bash
cat OUTPUT_DIRECTORY/summary.txt
```

```bash
cat OUTPUT_DIRECTORY/validation.txt
```

For structured details:

```bash
cat OUTPUT_DIRECTORY/manifest.json
```

With `jq`:

```bash
jq . OUTPUT_DIRECTORY/manifest.json
```

List generated parts:

```bash
find OUTPUT_DIRECTORY -maxdepth 1 -type f -name '*.md' -print | sort
```

Check file sizes:

```bash
du -h OUTPUT_DIRECTORY/*
```

## Re-running

You may run the same command again.

Because output names are now semantic and can change when part membership changes, use a dedicated output directory for each corpus and clear or replace that directory before a fresh run if you do not want older generated Markdown files retained.

## Help

Show all CLI options:

```bash
uv run mdmerge --help
```

Current CLI form:

```text
usage: mdmerge [-h] --token-limit TOKEN_LIMIT
               [--reserve-tokens RESERVE_TOKENS]
               [--model MODEL | --encoding ENCODING_NAME]
               input_directory output_directory
```

## Development and verification

Install development dependencies:

```bash
uv sync --group dev
```

Run the complete project quality pipeline:

```bash
./quality.sh
```

It verifies:

```text
Ruff formatting
Ruff lint
Mypy strict type checking
Pytest
CLI help
Direct entry point
```

Run checks individually:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run --group dev python -m pytest
uv run mdmerge --help
uv run python main.py --help
```

## Troubleshooting

### No Markdown files found

The input directory contains no recursively discoverable `.md` files.

### Input path is not a directory

Pass a directory, not a single Markdown file.

### OUTPUT_DIRECTORY must be outside INPUT_DIRECTORY

Choose a sibling or otherwise separate output directory.

### Source file exceeds the effective token limit

One complete source file is too large for the configured planning budget.

Increase `--token-limit`, reduce `--reserve-tokens`, or handle that source file separately.

### Unknown model

If tiktoken does not recognize a model name, use a supported model name or specify an encoding explicitly:

```bash
--encoding o200k_base
```

### Validation failed

Inspect:

```bash
cat OUTPUT_DIRECTORY/validation.txt
```

The final written files are re-tokenized, so validation is the authoritative result.

## Scope

markdownMerge is intentionally small.

It does not attempt to:

- upload files to an AI service
- call OpenAI, Gemini, Grok, Copilot, or another remote model API
- infer platform upload limits
- choose a token limit for you
- modify source content
- summarize sources
- split oversized source files
- perform semantic clustering
- act as a crawler

It takes an input Markdown corpus and a token budget and produces fewer validated Markdown files.

## License

MIT License
