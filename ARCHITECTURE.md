# Architecture

How the USD Unreal Pipeline validator is organized, how a validation run flows, and how rules plug in.

## Goals

- Keep execution, rules, configuration, and reporting in separate layers.
- Group rules by **domain/context** packages (`filesystem`, `geometry`, `textures`, `unreal`).
- Make adding a rule a small, local change — not a rewrite of the runner or CLI.
- Stay practical: explicit imports and contracts first; no plugin scanning.

## Package map

```
pipeline/
├── cli/           # Typer commands; wires the run together
├── config/        # Defaults, JSON overrides, .env loading
├── validation/    # Discovery, runner, shared result models
├── rules/
│   ├── validation_rule.py   # shared rule contract
│   ├── registry.py          # @register_rule + build_rules
│   ├── filesystem/          # live on-disk rules
│   ├── geometry/            # reserved
│   ├── textures/            # reserved
│   └── unreal/              # reserved
└── logging/       # Terminal rendering of validation results
```

| Layer | Owns | Does not own |
|---|---|---|
| `cli` | Command entry, exit codes | Rule logic, formatting details |
| `config` | Category toggles, per-rule settings | Whether a file passes |
| `validation` | File discovery, running rules, result types | How each rule decides pass/fail |
| `rules` | Checks, category packages, registration | Printing, CLI flags |
| `logging` | Human-readable output | Changing validation outcomes |

## End-to-end flow

```text
explore
  → load .env + config
  → resolve directory
  → discover files (recursive)
  → build_rules(config)
       → import category packages (decorator registration runs)
       → keep rules whose category + rule are enabled
       → construct via RuleClass.from_settings(settings)
  → validate_files(files, rules)
       → for each rule: applies_to(file)? validate(file)
  → render_results(...)  # per-file details + totals + By Category
  → exit 0/1
```

## Categories vs rules

**Category** = domain/context. Owned by a category package + base class:

| Package | Base class | Status |
|---|---|---|
| `rules/filesystem/` | `FilesystemRule` | Live |
| `rules/geometry/` | `GeometryRule` | Reserved |
| `rules/textures/` | `TexturesRule` | Reserved |
| `rules/unreal/` | `UnrealRule` | Reserved |

**Rule** = one specific check inside a category (`file_format`, `file_size`, `file_name`).

Concrete rules subclass the category base (so category identity comes from the package base, not ad-hoc labels).

Enable/disable whole categories in config:

```json
{
  "categories": {
    "filesystem": true,
    "geometry": false,
    "textures": false,
    "unreal": false
  }
}
```

A rule runs only if its category is enabled **and** `rules.<name>.enabled` is true.

## Registration and construction

Two separate concerns:

1. **Registration** — `@register_rule` adds the class to an in-memory list when the module is imported.
2. **Construction** — `from_settings(settings)` on the rule class maps config → instance.

Bootstrap matters: decorators only run if the module is imported. Each category package `__init__` imports its rule modules. `build_rules` calls `load_rule_packages()` to import category packages in a stable order.

If you add a rule module and forget to import it from the category `__init__`, it will **not** register.

There is no package scanning and no plugin entry-point discovery.

## Conditional skip

Optional per-rule `apply_to_extensions` (list of suffixes). Empty/missing means the rule applies to all files. The runner calls `rule.applies_to(file)` before `validate`.

## Result model and output

Rules own outcome vocabulary in `pipeline/rules/models.py`:

- `RuleCategory`, `Severity`, `RuleResult`

Validation owns file-level aggregation in `pipeline/validation/models.py`:

- `FileValidationResult` (collects `RuleResult` values for one file)

A file fails only on `error`.

Detail lines:

```text
[PASS]      path\to\asset.usd
          - [filesystem] file_format (info): Allowed file format
```

Summary includes overall totals plus a `By Category` section (checks / errors / warnings) for categories that emitted results.

## How to add a rule

1. Create `pipeline/rules/<category>/<rule>.py`.
2. Subclass that category’s base (e.g. `FilesystemRule`).
3. Set `name`, implement `from_settings` and `validate`, decorate with `@register_rule`.
4. Import the module from `pipeline/rules/<category>/__init__.py` so the decorator runs.
5. Add defaults under `rules.<name>` in `pipeline/config/defaults.py`.

You should not need to edit `runner.py` or `cli/app.py`.

## What is intentionally out of scope right now

- Geometry content checks (manifold, winding)
- Texture content checks
- Unreal Engine integration
- Automatic plugin discovery

Reserved category packages exist so those domains have a clear home later.

## Related docs

- [README.md](README.md) — setup and how to run
- `spdd/` — design history for how decisions were made
