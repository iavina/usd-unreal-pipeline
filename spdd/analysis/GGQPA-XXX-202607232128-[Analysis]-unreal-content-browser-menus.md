# SPDD Analysis: Unreal Content Browser Validation Menus

## Original Business Requirement

Add Unreal Content Browser context menus so artists/TDs can:

1. Right-click a **folder** and run validation on that folder’s contents.
2. Right-click **individual assets** (or a multi-selection) and run validation on those assets only.

Organization goal: keep the project easy to understand — the validator stays a clear module; Unreal interaction is layered (validation host vs editor UX) and calls into the validator rather than reimplementing it.

Constraints and engine facts to honor:

- Content Browser actions use Unreal’s `ToolMenuEntryScript` mechanism: subclass marked as a UClass, override `execute` (menu system injects `context` — never construct it), then `init_entry` + `register_menu_entry` to attach to a menu.
- Editor startup can auto-run `init_unreal.py` when its directory is on `UE_PYTHONPATH`.
- Folder selection paths may use a Content Browser `/All/...` prefix that must be normalized to package paths the validator understands (`/Game/...`).
- Known menu anchors: folder context `ContentBrowser.FolderContextMenu` (section such as `PathViewFolderOptions`); asset context `ContentBrowser.AssetContextMenu` (section chosen for the target UE version).
- Registration failures must not crash editor startup.
- Host / entrypoint ≠ rule category; menus are host UX only.
- Unreal keeps one Python interpreter per editor session; `pipeline*` reload must remain workable.
- Existing Execute Python Script entry (`scripts/unreal_validate.py`) and shared config (`scripts/unreal_validate_config.json`) remain valid.
- Results continue to use the existing Unreal Output Log formatting / emit path — no second report model.

Success criteria:

- Folder and asset context menus invoke validation for the correct selection scope.
- Menus register automatically on editor start via startup hook / `UE_PYTHONPATH`.
- Editor UX stays outside the installable validator package; the Unreal *validation host* may grow a small API so menus stay thin.
- CLI/`uv` remains unaffected.

## Domain Concept Identification

### Existing Concepts (from codebase)

- Unreal Host Entry: `pipeline.unreal.run_validation(config_path, content_root)` discovers recursively under one package path, builds rules, validates, emits log lines; returns overall pass bool.
- Unreal Context: `UnrealContext(asset_path)` discovers under a Content Browser package path via Asset Registry (`recursive_paths=True`); also exposes `get_asset_metadata(path)` for a single object path.
- Shared Runner: `validate_assets(assets, rules, ctx)` accepts an explicit asset list — already suitable for single/multi-asset runs if the caller supplies the list.
- Config / Rules / Report: JSON-merged config (including `host.content_root`), `build_rules`, `format_results`, Unreal `emit_lines` — reused by the current Execute Script entry.
- Execute Script Bootstrap: `scripts/unreal_validate.py` adds repo root to `sys.path`, clears `pipeline*` from `sys.modules`, then calls `run_validation` with the sidecar config.
- Module Reload Behavior: documented in `ARCHITECTURE.md`; editor session caches imports until purged or editor restart.

### New Concepts Required

- Editor Startup Hook: `init_unreal.py` loaded via `UE_PYTHONPATH` on every editor start; owns menu registration side effects only.
- Content Browser Menu Glue: `ToolMenuEntryScript` subclasses for folder and asset context menus (register, resolve selection, invoke validation).
- Selection Scope: The set of targets for one menu action — selected folder package path(s) and/or selected asset object path(s), distinct from config default `content_root`.
- Path Normalization: Mapping Unreal UI paths (e.g. `/All/Game/...`) to validator package paths (`/Game/...`); asset paths to object paths the host can resolve.
- Asset-Scoped Host Invocation: A way to validate an explicit asset list without pretending the selection is a recursive folder root (today only folder scoping is first-class on `run_validation`).

### Key Business Rules

- Menus are host UX; they must not embed rule policy beyond loading the existing Unreal sidecar config.
- Folder validation scopes discovery to the selected folder(s); asset validation scopes to the selected asset(s) only.
- `execute(context)` receives Unreal-injected context; callers never construct it.
- Registration failures must log clearly and must not crash editor startup.
- Iterative Python edits under `pipeline/` should remain reloadable from menu actions the same way Execute Script reloads today.
- CLI/`uv` must remain unaffected; menu code must not be required outside the editor.

## Strategic Approach

### Solution Direction

Treat three layers:

1. **Validator** — `pipeline` core/rules/config/report (host-agnostic).
2. **Unreal validation host** — `pipeline/unreal` (`run_validation`, context, emit).
3. **Unreal editor UX** — `scripts/startup` (startup hook + Content Browser menus).

Menus resolve selection, normalize paths, then call the Unreal host. They do not reimplement discovery, rules, or reporting.

High-level flow:

```text
Editor start (UE_PYTHONPATH → init_unreal.py)
  → register ToolMenuEntryScript entries

User right-clicks folder/assets → execute(context)
  → resolve selection → normalize paths
  → purge pipeline* for reload
  → run_validation for that scope
  → emit shared result lines to Output Log
```

### Key Design Decisions

- **Where menus live**: `scripts/startup/` — editor chrome only; not inside the installable package. → **Locked.**
- **How folder validation is invoked**: `run_validation(..., content_root=selected_folder)`. → **Locked.**
- **How asset validation is invoked**: extend `run_validation` with `asset_paths=` (Option B) so one host API serves both scopes. → **Locked** (organization over avoiding all `pipeline/` diffs).
- **Config source**: reuse `scripts/unreal_validate_config.json`. → **Locked.**
- **Reload strategy**: purge `pipeline*` before importing/calling the host from menu `execute`. → **Locked.**
- **Startup failure handling**: soft-fail registration with clear log. → **Locked.**
- **Multi-select**: one host call per selected folder; one combined host call for a multi-asset selection. → **Locked in REASONS Canvas.**

### Alternatives Considered

- **Duplicate host orchestration in scripts for assets only**: works without touching `pipeline/unreal`, but duplicates config/rules/format/emit and drifts easily — rejected for organization.
- **Menus inside `pipeline/unreal/`**: couples the library to editor menu side effects — rejected.
- **Folders-only first slice**: defers asset UX — rejected; both scopes are in requirement.
- **Separate menu-only config**: extra policy surface — rejected.

### Recommendation for this cycle

**Option B (locked):** extend `pipeline.unreal.run_validation` with asset-scoped paths; keep ToolMenu / `init_unreal` under `scripts/startup/`; menus call only the Unreal host API.

## Risk & Gap Analysis

### Requirement Ambiguities

- Exact asset-menu section name for the project’s Unreal Engine version (verify during implementation).
- Whether `UE_PYTHONPATH` is set as an env var only, or also via project Python path / Content/Python shim — document the chosen wiring.
- Final menu labels (“Validate Folder” / “Validate Assets”).

### Edge Cases

- No selection / empty selection when the menu fires.
- Mixed selection (folders + assets) — folder menu vs asset menu own their own selection APIs.
- Selected folder path forms: `/All/Game/...` vs `/Game/...` vs other mounts (`/Engine`, plugins).
- Selected asset path forms: package path vs object path (`/Game/Foo/Bar.Bar`).
- Very large folder selections (performance / log volume).
- Assets that fail metadata resolution.
- Re-registering menus on multiple `init_unreal` executions (duplicate entries).

### Technical Risks

- **Host API completeness**: asset scope is not first-class on `run_validation` today — mitigated by the locked `asset_paths` extension.
- **UClass / menu script lifetime**: menu types persist; validator reload must purge only `pipeline*`.
- **Import path under Unreal**: startup directory on `UE_PYTHONPATH` still needs repo root on `sys.path` to import `pipeline`.
- **Editor version drift**: menu names/sections differ across UE versions — soft-fail registration; verify against project UE version.

### Acceptance Criteria Coverage

| AC# | Description | Addressable? | Gaps/Notes |
|-----|-------------|--------------|------------|
| 1 | Folder context menu validates selected folder(s) | Yes | Normalize `/All` prefix |
| 2 | Asset context menu validates selected asset(s) | Yes | Via `asset_paths` on host API |
| 3 | Auto-register on editor start | Yes | Document `UE_PYTHONPATH` wiring |
| 4 | Editor UX outside installable package | Yes | Host API may still extend |
| 5 | Reuse existing results/logging | Yes | Call shared format/emit only |
| 6 | Clear layering (validator / host / UX) | Yes | Locked in Approach |
| 7 | Preserve Execute Script entry | Yes | Menus are additive |

Decision status: **Option B locked**; REASONS Canvas should implement that direction without copying external tutorial scripts.
