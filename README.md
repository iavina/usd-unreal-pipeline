# USD Unreal Pipeline

Validator for USD / content pipelines. Runs from the `pipeline` CLI, or from Unreal Engine editor Python through a shared validation core.

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

```env
PIPELINE_DEV_DIRECTORY=C:\path\to\assets
PIPELINE_UNREAL_EDITOR=C:\Path\To\UnrealEditor.exe
PIPELINE_UNREAL_PROJECT=C:\Path\To\YourGame.uproject
# optional override for Cmd:
# PIPELINE_UNREAL_EDITOR_CMD=C:\Path\To\UnrealEditor-Cmd.exe
```

After `uv sync`, the `pipeline` console script is installed in the project venv:

```powershell
.\.venv\Scripts\Activate.ps1   # Windows
pipeline --help
```

Without activating, you can still use `uv run pipeline …` as a shortcut into that same venv.

## Entry points (end setup)

### 1. Filesystem validate (CLI, no Unreal)

```bash
pipeline validate
pipeline validate C:\path\to\assets
pipeline validate --config path\to\config.json
```

| Arg / env | Meaning |
|---|---|
| `directory` | Folder of files to scan (or `PIPELINE_DEV_DIRECTORY`) |
| `--config` / `-c` | Optional JSON config |

### 2. Interactive Unreal (menus)

```bash
pipeline editor --editor C:\Path\To\UnrealEditor.exe --project C:\Path\To\Game.uproject
# or from .env:
pipeline editor
```

Opens the editor. If `UE_PYTHONPATH` is unset, sets it to `<repo>/scripts/startup` so `init_unreal.py` registers Content Browser menus.

Then in the editor: right-click folder → **Validate Folder**, or assets → **Validate Assets**.

| Arg / env | Meaning |
|---|---|
| `--editor` / `-e` | `UnrealEditor.exe` (or `PIPELINE_UNREAL_EDITOR`) |
| `--project` / `-p` | `.uproject` (or `PIPELINE_UNREAL_PROJECT`) |
| `UE_PYTHONPATH` | Python **startup script** folders (not the editor). Left alone if already set. |

### 3. Unreal one-shot validate (Cmd, then exit)

```bash
pipeline editor --cmd --editor C:\Path\To\UnrealEditor.exe --project C:\Path\To\Game.uproject
```

Uses `UnrealEditor-Cmd` (derived from `--editor`, or `--editor-cmd` / `PIPELINE_UNREAL_EDITOR_CMD`), runs `scripts/unreal_run_validation.py`, waits, exits. No menus.

| Arg / env | Meaning |
|---|---|
| `--cmd` | One-shot Cmd mode |
| `--editor-cmd` | Explicit `UnrealEditor-Cmd.exe` (optional) |
| `--project` | `.uproject` (required) |

### 4. Menus-only Execute Script fallback

If the editor was opened without `UE_PYTHONPATH`, run **Execute Python Script** → `scripts/unreal_validate.py`. Registers menus only; does not validate.

### 5. Host API (inside Unreal Python)

`pipeline.unreal.run_validation(config_path=..., content_root=...)` or `asset_paths=[...]`.

Config for Unreal host/menu/Cmd runs: `scripts/unreal_validate_config.json`.

### Path cheat sheet

| Name | What it is |
|---|---|
| Editor path | `UnrealEditor.exe` (interactive UI) |
| Editor Cmd path | `UnrealEditor-Cmd.exe` (automation; exits after script) |
| Project path | `YourGame.uproject` |
| `UE_PYTHONPATH` | Where Unreal looks for `init_unreal.py` — **not** the editor |

## Docs

- [ARCHITECTURE.md](ARCHITECTURE.md) — package layout, context contract, Unreal boundary, how to add a rule
- [RULES.md](RULES.md) — available rules, settings, and outcomes
- `spdd/` — Structured Prompt-Driven Development design history

## Development

Project design and changes follow [Structured Prompt-Driven Development (SPDD)](https://martinfowler.com/articles/structured-prompt-driven/). Use `uv` for dependency management; run the installed `pipeline` CLI (or `uv run pipeline` without activating the venv).

Output uses shared emoji labels. CLI adds simple ANSI; Unreal uses log/warning/error channels (no ANSI).
