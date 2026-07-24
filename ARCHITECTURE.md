# Architecture

How the USD Unreal Pipeline validator is organized.

## Goals

- One shared validation runner for CLI (`uv`) and Unreal editor Python.
- Clear package ownership — no mixed CLI / Unreal / core concerns.
- Rules consume `AssetMetadata` and optionally `load_uobject`.
- Domain rule packages: `filesystem`, `geometry`, `textures`, `unreal`, `materials`.

## Package map

```text
pipeline/                 # installable validator + hosts
├── cli/                  # Typer validate + editor launch (split modules)
├── unreal/               # Unreal validation host (env, context, entry, emit)
├── core/                 # AssetMetadata, ValidationContext, FilesystemContext, runner
├── rules/                # Category packages of checks
├── config/               # Defaults + JSON overrides
└── report/               # Shared result formatting (+ optional CLI ANSI)

scripts/
├── unreal_validate.py         # Menus-only Execute Script fallback
├── unreal_run_validation.py   # Cmd / automation: run validation once
├── unreal_validate_config.json
└── startup/                   # Unreal editor UX (not part of the installable package)
    ├── init_unreal.py    # UE_PYTHONPATH startup hook
    ├── register_menus.py # Content Browser ToolMenu entries
    ├── bootstrap.py      # sys.path + pipeline* reload
    └── paths.py          # Content Browser path normalization
```

| Layer | Owns | Does not own |
|---|---|---|
| `pipeline` core/rules/config/report | Validation policy and shared runner | Editor menus |
| `pipeline/cli` | CLI `validate` + `editor` (+ `--cmd`) | Rule logic, ToolMenus |
| `pipeline/unreal` | Unreal validation host (`run_validation`, context, emit) | Content Browser menus / ToolMenus |
| `scripts/startup` | Editor UX (startup + context menus) | Rule policy, discovery internals |

## Context contract

`AssetMetadata` is the currency (path, name, extension, size_bytes, asset_class, extra).

`ValidationContext` stays small:

- `get_assets() -> list[AssetMetadata]`
- `get_asset_metadata(path) -> AssetMetadata | None`
- `load_uobject(path) -> Any` — filesystem always `None`; Unreal loads the asset

`UnrealContext` raises `ImportError` at construction if Unreal is unavailable.

## Unreal boundary

[`pipeline/unreal/env.py`](pipeline/unreal/env.py) sets `UNREAL_AVAILABLE` once at import (cached in `sys.modules`). Unreal-only rules guard with that flag and emit an explicit skipped `RuleResult` (skips never fail the asset). When available, they call `ctx.load_uobject(path)` and run engine APIs in the rule module. Wrong asset types return no results (no spam).

### Unreal surfaces

1. **CLI interactive** — `pipeline editor --editor <UnrealEditor> --project <Game.uproject>`
   - Sets `UE_PYTHONPATH` to `scripts/startup` when unset (`UE_PYTHONPATH` ≠ editor binary)
2. **CLI Cmd one-shot** — `pipeline editor --cmd ...` runs [`scripts/unreal_run_validation.py`](scripts/unreal_run_validation.py) via `UnrealEditor-Cmd` and exits
3. **Validation host** — `pipeline.unreal.run_validation(config_path, content_root=None, asset_paths=None)`
4. **Editor UX** — `scripts/startup/` Content Browser menus call the host
5. **Execute Script fallback** — [`scripts/unreal_validate.py`](scripts/unreal_validate.py) registers menus only

### Module reload (editor session)

Unreal Editor keeps one embedded Python interpreter for the whole session. A normal `import` only loads a module the first time; later runs reuse the object in `sys.modules`, so disk edits appear stale until the editor restarts.

[`scripts/startup/bootstrap.py`](scripts/startup/bootstrap.py) deletes every `pipeline` / `pipeline.*` entry from `sys.modules` **before** importing the package. Execute Script and Content Browser menu actions both use that helper. Nested imports then reload from disk automatically. Restart the editor only if non-Python editor state or a stubborn cache remains. Do not purge the engine `unreal` module.

## Flow

```text
Host (cli validate | editor [--cmd] | unreal run_validation | Content Browser menu)
  → load config
  → build context (FilesystemContext | UnrealContext)
  → assets = ctx.get_assets()  OR  resolve asset_paths via get_asset_metadata
  → build_rules(config)
  → validate_assets(assets, rules, ctx)
  → format / emit results
```

Host ≠ category: running in Unreal does not force only `rules/unreal/`. Enable categories in config.

Unreal scan root for folder-scoped runs: `host.content_root` in JSON config (default `/Game/ExampleContent`), or an explicit `content_root=` / selected folder from the menu.

## How to add a rule

1. Create `pipeline/rules/<category>/<rule>.py`.
2. Subclass `ValidationRule`, set `category = RuleCategory.<X>`.
3. Implement `from_settings` and `validate(asset, ctx)`.
4. Load shared filters via `common_filter_kwargs(settings)` (`apply_to_extensions`, `rule_ignore`).
5. Prefer metadata fields; for engine objects use `ctx.load_uobject` after an `UNREAL_AVAILABLE` guard when needed.
6. Add defaults under `rules.<name>` in `pipeline/config/defaults.py` (include `rule_ignore: []`).
7. Document the rule in [RULES.md](RULES.md).

## Related docs

- [README.md](README.md) — setup and how to run
- [RULES.md](RULES.md) — built-in rule catalog and settings
- `spdd/` — design history
