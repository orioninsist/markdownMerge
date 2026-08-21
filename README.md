# 🚀 Project Overview

**markdownMerge** is now a production-ready Markdown processing and merging system designed for very large documentation collections.

The system reads thousands of Markdown files, cleans them, preserves file boundaries, calculates exact tokens using **tiktoken**, and automatically creates optimized output parts based on a user-defined token limit.

The key design principle:

> **Files are never manually split or modified. The system only decides where a new output part starts based on token capacity.**

---

# ✅ Final Architecture

```
Markdown Files
      |
      v
+----------------+
| File Discovery |
+----------------+
      |
      v
+----------------+
| Markdown Clean |
+----------------+
      |
      v
+----------------+
| Token Counter  |
|   tiktoken     |
+----------------+
      |
      v
+----------------+
| Source Segment |
| 1 file = 1 unit|
+----------------+
      |
      v
+----------------+
| Token Packing  |
| Smart grouping |
+----------------+
      |
      v
+----------------+
| Output Writer  |
| Part creation  |
+----------------+
      |
      v
+----------------+
| Manifest JSON  |
+----------------+
```

---

# 🎯 Core Behavior

## Before

```
100 Markdown files

Manual decision:
    "Split every 10 files"
    "Split every folder"
    "Guess size"

Problems:
    ❌ Uneven token sizes
    ❌ Manual work
    ❌ Possible context overflow
    ❌ Files may be broken
```

---

## Now

```
100 Markdown files

User gives:

--token-limit 1500000


System calculates:

File 1
+ File 2
+ File 3
+ ...
+ File N

until:

Current tokens + next file > limit


Then:

Create new Part

Continue automatically
```

Result:

```
Part 01
├── file001.md
├── file002.md
├── file003.md
└── ...

Part 02
├── next files
└── ...

Part 03
└── ...
```

---

# 🔒 File Safety Rules

## Guaranteed

| Feature                         | Status      |
| ------------------------------- | ----------- |
| Original Markdown files changed | ❌ Never     |
| Files deleted                   | ❌ Never     |
| File content modified           | ❌ Never     |
| File split into pieces          | ❌ Never     |
| File moved between parts        | ❌ Never     |
| Token calculation               | ✅ Exact     |
| Output optimization             | ✅ Automatic |

---

# 🧠 Token Packing Logic

Example:

User:

```bash
--token-limit 1500000
```

System:

```
File A
500,000 tokens

+
File B
400,000 tokens

+
File C
550,000 tokens

----------------

Total:
1,450,000 tokens

OK
Add to Part 1


Next file:

200,000 tokens


1,450,000 + 200,000

= 1,650,000

Too large


STOP

Create Part 2
```

Result:

```
Part 1
==========
File A
File B
File C

1,450,000 tokens


Part 2
==========
File D
...
```

---

# 📊 Real Production Test Result

Input:

```
OpenAI Documentation Dataset
```

Processed:

| Metric               |      Result |
| -------------------- | ----------: |
| Directories scanned  |       1,947 |
| Markdown files found |      21,966 |
| Processed files      |      21,966 |
| Failed files         |           0 |
| Skipped files        |           0 |
| Original characters  | 185,142,126 |
| Cleaned characters   | 184,646,014 |
| Source tokens        |  47,300,852 |
| Output tokens        |  49,753,006 |
| Generated parts      |          36 |
| Generated segments   |      21,966 |
| Split files          |           0 |
| Warnings             |           0 |

---

# 📦 Output Example

Generated:

```
Openai_Academy_Part_01_of_36.md

Openai_Academy_Part_02_of_36.md

Openai_Academy_Part_03_of_36.md

...

Openai_Academy_Part_36_of_36.md
```

---

# 📄 Output Structure Example

```markdown
# Markdown Merge — Part 01


## Table of Contents


- academy.openai.com/code-of-conduct.md
- academy.openai.com/resources/team.md
- ...


---

## Source: `academy.openai.com/code-of-conduct.md`

<!-- source-path: academy.openai.com/code-of-conduct.md -->

Markdown content...


---

## Source: `academy.openai.com/resources/team.md`

Markdown content...
```

---

# 🧪 Quality Verification

Final checks:

| Check       | Result   |
| ----------- | -------- |
| Ruff format | ✅ Passed |
| Ruff lint   | ✅ Passed |
| Mypy strict | ✅ Passed |
| Pytest      | ✅ Passed |
| Coverage    | ✅ 86.95% |
| Smoke test  | ✅ Passed |

---

# 🚀 Usage

## Basic Merge

```bash
mdmerge ./docs ./output
```

---

## Token Controlled Merge

```bash
mdmerge ./docs ./output \
--token-limit 1500000
```

Meaning:

```
Maximum output part size:
1,500,000 tokens
```

---

## Custom Encoding

Default:

```
o200k_base
```

Example:

```bash
mdmerge ./docs ./output \
--encoding o200k_base
```

---

## Custom Output Name

Example:

```bash
mdmerge ./docs ./output \
--output-prefix OpenAI_Docs
```

Creates:

```
OpenAI_Docs_Part_01_of_XX.md
```

---

## Full Example

```bash
mdmerge \
/mnt/local/resources/openai/docs/ \
/mnt/local/resources/openai/_merge/ \
--token-limit 1500000 \
--output-prefix Openai_Academy \
--encoding o200k_base
```

---

# 📜 Manifest Output

Generated:

```
merge_manifest.json
```

Contains:

```json
{
  "processed_source_files": 21966,
  "generated_segments": 21966,
  "output_parts": 36,
  "oversized_sources_split": 0
}
```

This provides:

* Audit trail
* Reproducibility
* File tracking
* Token statistics

---

# 🏆 Final Project Result

```
Before:

Manual Markdown merging
        |
        v
Guess file count
        |
        v
Risk of oversized context


After:

Markdown Collection
        |
        v
Automatic Discovery
        |
        v
Exact Token Counting
        |
        v
Atomic File Packing
        |
        v
Optimized AI Context Files
```

## Final Status

```
markdownMerge v1.0.0

STATUS: PRODUCTION READY ✅
```

A large documentation collection can now be converted into AI-optimized Markdown context files with one command.
