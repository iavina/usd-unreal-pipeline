# USD Unreal Pipeline

Validator for USD / content pipelines. Runs from the CLI via `uv`, or from Unreal Engine editor Python through a shared validation core.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- A directory of assets to explore — Pixar's [Kitchen Set](https://openusd.org/release/dl_kitchen_set.html) works well for CLI smoke tests
- Optional: Unreal Editor with Python enabled, for the Unreal host

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

## Usage (CLI)

Discover files recursively and validate them against enabled rules:

```bash
uv run pipeline explore
uv run pipeline explore C:\path\to\assets
uv run pipeline explore --config path\to\config.json
```

Optional JSON config overrides defaults (category toggles, rule enablement, allowed extensions, size thresholds, naming options). See [RULES.md](RULES.md) for the built-in catalog. Defaults enable filesystem rules (USD-like extensions, 100 MB max / 80 MB warn, no spaces in names) and leave `geometry` / `textures` / `unreal` off for CLI.

Exit code `0` when all assets pass; `1` when any asset fails. Skipped Unreal-only checks (when the editor module is absent) do not fail the run.

## Usage (Unreal)

In the editor, use **Execute Python Script** and choose:

`scripts/unreal_validate.py`

That script bootstraps `sys.path`, loads `scripts/unreal_validate_config.json` (enables `unreal`, `geometry`, and `textures`), and validates assets under the path in `host.content_root` (default `/Game/ExampleContent`). Change that field to scan a different Content Browser folder. Output goes to the Unreal log.

## Docs

- [ARCHITECTURE.md](ARCHITECTURE.md) — package layout, context contract, Unreal boundary, how to add a rule
- [RULES.md](RULES.md) — available rules, settings, and outcomes
- `spdd/` — Structured Prompt-Driven Development design history

## Development

Project design and changes follow [Structured Prompt-Driven Development (SPDD)](https://martinfowler.com/articles/structured-prompt-driven/).

Output uses shared emoji labels. CLI adds simple ANSI; Unreal uses log/warning/error channels (no ANSI).
