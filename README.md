# USD Unreal Pipeline

CLI for discovering and validating USD asset directories. Domain-specific rules beyond filesystem checks are planned; geometry, texture, and Unreal validation are not implemented yet.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A USD directory to explore — if you do not have one handy, Pixar's [Kitchen Set](https://openusd.org/release/dl_kitchen_set.html) sample scene works well

## Setup

```bash
git clone <repo-url>
cd pipeline
uv sync
cp .env.example .env   # Windows: copy .env.example .env
```

Edit `.env` and set a default explore directory:

```env
PIPELINE_DEV_DIRECTORY=C:\path\to\assets
```

## Usage

Discover files recursively and validate them against enabled rules:

```bash
uv run pipeline explore
uv run pipeline explore C:\path\to\assets
uv run pipeline explore --config path\to\config.json
```

Optional JSON config overrides defaults (rule enablement, allowed extensions, size thresholds, naming options). Built-in defaults allow `.usd`, `.usda`, `.usdc`, `.usdz` up to 100 MB, warn above 80 MB, and forbid spaces in filenames.

Exit code `0` when all files pass; `1` when any file fails.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for package layout, validation flow, rule categories, and how the registry fits in.

Short version: `cli` orchestrates; `config` supplies category/rule settings; `rules` are grouped by category packages; `validation` discovers files and runs rules; `logging` prints structured results. See Architecture for `@register_rule`, `from_settings`, and how to add a rule.

## Development

Project design and changes follow [Structured Prompt-Driven Development (SPDD)](https://martinfowler.com/articles/structured-prompt-driven/). Prompts and analysis live under `spdd/`.

Styled terminal output uses color and status icons when supported. Set `NO_COLOR=1` to disable styling.
