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
| `materials` | off | Needs Unreal; named-parameter PBR / normals on MaterialInterface |

Unreal execute script ([`scripts/unreal_validate_config.json`](scripts/unreal_validate_config.json)) turns on `geometry`, `textures`, `unreal`, and `materials`, turns off `filesystem`, and sets `host.content_root` (default `/Game/ExampleContent`). That config also sets `rule_ignore` on the materials rules for `/Game/ExampleContent/UMG/**` and `/Game/ExampleContent/Substrate/**`.

Materials rules assume a shared parent Material + Material Instances with stable parameter names (defaults: `BaseColor`, `Metallic`, `Roughness`, `Normal`). Hardwired constants without those parameters fail PBR checks when the material is PBR-shaped (see `material_is_pbr`).

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

### materials

| Rule | Settings | Behavior |
|---|---|---|
| `material_is_pbr` | `shading_models` (`DefaultLit`), `blend_modes` (`Opaque`), `base_color_vector_name` / `base_color_texture_name` (`BaseColor`), `metallic_name` / `roughness_name`, min/max ranges `[0,1]` | PBR shape gate: Surface + allowlisted shading/blend. If not PBR-shaped → `[SKIPPED]` with reason (does not fail the asset). If PBR-shaped → require BaseColor vector **or** texture; Metallic/Roughness present and in range. Also skips when Unreal/MEL unavailable. Non-materials → no result |
| `material_normals_ok` | `normal_texture_name` (`Normal`), `require_tangent_space` (true), `require_normal_map` (false), `require_linear_normal_map` (true) | Tangent-space when required; missing Normal errors only if required; bound Normal must be non-sRGB when linear required. Skip when Unreal/MEL unavailable. Non-materials → no result |

## Shared rule options

Every rule accepts:

- `enabled` (bool) — rule must be enabled and its category must be on
- `apply_to_extensions` (list) — empty means all assets; otherwise filter by `AssetMetadata.extension`
- `rule_ignore` (list of globs) — empty means none; matching paths are out of scope for the rule (quiet not-applicable: no results). Supports `*`, `?`, and `**` (e.g. `/Game/UI/**`, `**/Fonts/**`). Ignored ≠ policy pass and ≠ host `[SKIPPED]`.

## Outcomes

- **Error** — fails the asset (CLI exit `1` if any asset fails)
- **Warning** / **Info** — do not fail the asset
- **Skipped** (`RuleResult.skipped`) — never fails the asset; counted in the summary. Used when:
  - Unreal / MaterialEditingLibrary is unavailable for an Unreal-only rule
  - `material_is_pbr` decides the material is not PBR-shaped (domain / shading model / blend mode outside the configured allowlists) — message starts with `Not detected as PBR ...`

## Adding a rule

See [ARCHITECTURE.md](ARCHITECTURE.md) → How to add a rule. Keep this catalog in sync when you add or rename rules.
