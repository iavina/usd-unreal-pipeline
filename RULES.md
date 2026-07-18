# Validation rules

Catalog of built-in rules. Enable categories and tune settings via JSON config (merged over [`pipeline/config/defaults.py`](pipeline/config/defaults.py)).

Host ≠ category: running under Unreal does not force only `unreal` rules. Toggle categories in config.

## Categories (defaults)

| Category | Default (CLI) | Notes |
|---|---|---|
| `filesystem` | on | Disk / path metadata checks |
| `geometry` | off | Needs Unreal; skips if `UNREAL_AVAILABLE` is false |
| `textures` | off | Needs Unreal; skips if `UNREAL_AVAILABLE` is false |
| `unreal` | off | Path policy for Unreal object paths |

Unreal execute script ([`scripts/unreal_validate_config.json`](scripts/unreal_validate_config.json)) turns on `geometry`, `textures`, and `unreal`, turns off `filesystem`, and sets `host.content_root` (default `/Game/ExampleContent`).

## Rules

### filesystem

| Rule | Settings | Behavior |
|---|---|---|
| `file_format` | `allowed_extensions` (default `.usd` / `.usda` / `.usdc` / `.usdz`) | Error if extension not allowed |
| `file_size` | `warn_bytes` (80 MB), `max_bytes` (100 MB) | Warn above soft limit; error above max |
| `file_name` | `forbid_spaces` (true) | Error if filename contains spaces |

### geometry

| Rule | Settings | Behavior |
|---|---|---|
| `mesh_closed` | `require_closed` (true) | Static Mesh closedness via DynamicMesh. Open → error if required, else info. Ambiguous border loops → warning. Skip when Unreal unavailable. Non-meshes → no result |

### textures

| Rule | Settings | Behavior |
|---|---|---|
| `texture_max_resolution` | `max_resolution` (2048) | Error if max(width, height) exceeds limit. Skip when Unreal unavailable. Non-textures → no result |

### unreal

| Rule | Settings | Behavior |
|---|---|---|
| `unreal_path` | `require_prefix` (`/Game`), `forbid_spaces` (true) | Error if path has spaces or does not start with prefix |

## Shared rule options

Every rule accepts:

- `enabled` (bool) — rule must be enabled and its category must be on
- `apply_to_extensions` (list) — empty means all assets; otherwise filter by `AssetMetadata.extension`

## Outcomes

- **Error** — fails the asset (CLI exit `1` if any asset fails)
- **Warning** / **Info** — do not fail the asset
- **Skipped** (`RuleResult.skipped`) — Unreal-only rules when the editor module is absent; never fails the asset; counted in the summary

## Adding a rule

See [ARCHITECTURE.md](ARCHITECTURE.md) → How to add a rule. Keep this catalog in sync when you add or rename rules.
