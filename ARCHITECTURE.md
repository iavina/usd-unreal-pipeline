# Architecture

How the USD Unreal Pipeline validator is organized.

## Goals

- One shared validation runner for CLI (`uv`) and Unreal editor Python.
- Clear package ownership — no mixed CLI / Unreal / core concerns.
- Rules consume `AssetMetadata` and optionally `load_uobject`.
- Domain rule packages: `filesystem`, `geometry`, `textures`, `unreal`.

## Package map

```text
pipeline/
├── cli/         # Typer, dotenv, directory resolve, terminal print
├── unreal/      # env (UNREAL_AVAILABLE), UnrealContext, entry, log emit
├── core/        # AssetMetadata, ValidationContext, FilesystemContext, runner
├── rules/       # Category packages of checks
├── config/      # Defaults + JSON overrides
└── report/      # Shared result formatting (+ optional CLI ANSI)
```

| Package | Owns | Does not own |
|---|---|---|
| `cli` | Entrypoint, env, dir resolve, print | Rule logic, Unreal |
| `unreal` | Availability flag, context, entry, log emit | Rule policy |
| `core` | Metadata, context ABC, filesystem context, runner | Host SDKs, printing |
| `rules` | Pass/fail/skip policy (+ Unreal APIs for Unreal-only rules) | Discovery, printing |
| `config` | Category/rule settings | Pass/fail |
| `report` | Shared result lines | Host SDKs |

## Context contract

`AssetMetadata` is the currency (path, name, extension, size_bytes, asset_class, extra).

`ValidationContext` stays small:

- `get_assets() -> list[AssetMetadata]`
- `get_asset_metadata(path) -> AssetMetadata | None`
- `load_uobject(path) -> Any` — filesystem always `None`; Unreal loads the asset

`UnrealContext` raises `ImportError` at construction if Unreal is unavailable.

## Unreal boundary

[`pipeline/unreal/env.py`](pipeline/unreal/env.py) sets `UNREAL_AVAILABLE` once at import (cached in `sys.modules`). Unreal-only rules guard with that flag and emit an explicit skipped `RuleResult` (skips never fail the asset). When available, they call `ctx.load_uobject(path)` and run engine APIs in the rule module. Wrong asset types return no results (no spam).

## Flow

```text
Host (cli explore | unreal run_validation)
  → load config
  → build context (FilesystemContext | UnrealContext)
  → assets = ctx.get_assets()
  → build_rules(config)
  → validate_assets(assets, rules, ctx)
  → format / emit results
```

Host ≠ category: running in Unreal does not force only `rules/unreal/`. Enable categories in config.

Unreal scan root: `host.content_root` in JSON config (default `/Game/ExampleContent`). The Execute Python Script entry stays no-arg; change the sidecar JSON (or pass `content_root=` to `run_validation`) to retarget discovery.

## How to add a rule

1. Create `pipeline/rules/<category>/<rule>.py`.
2. Subclass `ValidationRule`, set `category = RuleCategory.<X>`.
3. Implement `from_settings` and `validate(asset, ctx)`.
4. Prefer metadata fields; for engine objects use `ctx.load_uobject` after an `UNREAL_AVAILABLE` guard when needed.
5. Add defaults under `rules.<name>` in `pipeline/config/defaults.py`.
6. Document the rule in [RULES.md](RULES.md).

## Related docs

- [README.md](README.md) — setup and how to run
- [RULES.md](RULES.md) — built-in rule catalog and settings
- `spdd/` — design history
