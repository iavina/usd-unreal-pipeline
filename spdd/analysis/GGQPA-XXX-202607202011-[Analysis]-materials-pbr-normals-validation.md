# SPDD Analysis: Materials PBR and Normals Validation

## Original Business Requirement

Add Unreal-hosted validation for CAD→USD→Unreal materials, simplified to two concerns: whether materials are valid PBR, and whether normals are correct. Validation must use Unreal Engine’s Python API (Material / MaterialInterface / MaterialEditingLibrary patterns), not disk-side USD shade parsing in this cycle.

Agreed assumptions and scope from product discussion:

1. CAD source content is translated to USD; unclean materials break downstream Unreal look and shader cost. Prioritize a small, enforceable gate over a broad materials cleanliness suite.
2. “Valid PBR” means Surface-domain, Default Lit (or a small PBR shading-model allowlist), Opaque (or a configured blend allowlist), and core PBR channels present with sane ranges: base color, metallic ∈ [0, 1], roughness ∈ [0, 1].
3. “Correct normals” means tangent-space normals on the material, a bound normal map when expected, and that normal map treated as linear / non-sRGB.
4. Unreal Python can reliably read named material parameters (via MaterialEditingLibrary scalar/vector/texture getters), not hardwired constants plugged into material graph pins. Therefore this cycle assumes the import convention: shared parent Material + Material Instances with stable parameter names (e.g. BaseColor, Metallic, Roughness, Normal).
5. Fit the existing dual-host validator: new `materials` category (or equivalent), Unreal-only rules that skip when Unreal is unavailable, wrong asset types produce no results (no spam), defaults keep materials off for CLI, opt-in via Unreal execute-script config.
6. Follow existing Unreal-only rule precedent (`texture_max_resolution`, `mesh_closed`): `UNREAL_AVAILABLE` guard, `ctx.load_uobject`, engine APIs in the rule module, category-package discovery, config defaults, `RULES.md` documentation.

Out of scope for this cycle:

- Full material hygiene suite (dedupe names, unused materials, usage-flag minimization, MI-vs-Material preference as a separate product gate)
- Mesh tangent / topology normal correctness (geometry domain)
- USD PreviewSurface / MaterialX validation on disk in the CLI host
- Creating or repairing materials (validation only)
- Unreal editor menu/plugin UI

Success criteria:

- Materials checks are discoverable under a materials (or agreed) category when that category is enabled
- Under Unreal host, PBR validity and normals can be enforced via config (parameter name allowlist / expected names, ranges, optional require-normal-map)
- Non-parameterized materials (constants only, no named params) fail or warn in a defined way rather than silently passing as PBR
- Rules skip cleanly when Unreal is unavailable; non-material assets do not spam failures
- Default CLI unchanged when materials category stays off
- Existing filesystem / geometry / textures / unreal behavior remains unchanged when materials stays disabled

## Domain Concept Identification

### Existing Concepts (from codebase)

- Rule Categories: `filesystem`, `geometry`, `textures`, `unreal` in `RuleCategory` and config defaults; category-package discovery under `pipeline/rules/<category>/`. No `materials` category today.
- Validation Context: Small ABC — discover assets + `load_uobject`; Unreal-only rules own engine API calls after an availability guard (`ARCHITECTURE.md` Unreal boundary).
- Unreal Host: Soft dependency via `pipeline/unreal/env.py` (`UNREAL_AVAILABLE`); `UnrealContext` discovers Content Browser assets under `host.content_root`.
- Unreal-only rule precedent: `texture_max_resolution` (Texture2D size) and `mesh_closed` (StaticMesh / DynamicMesh) — skip when Unreal absent; wrong type → empty results; policy → `RuleResult` list.
- Textures category: Owns map-asset checks (resolution), not material bindings or shading model.
- Config / docs: `defaults.py` category toggles + per-rule settings; Unreal smoke config enables geometry/textures/unreal; `RULES.md` + `ARCHITECTURE.md` catalog domain packages (materials not listed yet).

### New Concepts Required

- Materials Category: New rule domain for Material / MaterialInstance (MaterialInterface) assets and PBR/normal policy.
- Valid PBR Material: Surface + PBR shading model + allowed blend + required named parameters present with values in configured ranges.
- Named Parameter Convention: Stable MI parameter names agreed with the CAD→USD→UE import path (base color, metallic, roughness, normal).
- Correct Normals (material sense): Tangent-space normal evaluation, bound normal texture parameter, normal texture not marked sRGB.
- PBR Parameter Completeness: Distinction between “parameter exists on the material interface” and “value is in range,” including failure mode when the convention is not followed.

### Key Business Rules

- Materials must look like PBR under the shared parent + MI convention; hardwired-only graphs are not considered validated PBR.
- Metallic and roughness must be in [0, 1] when readable as named scalars.
- Base color must be representable as a named vector and/or texture parameter (exact required shape is a config/design choice).
- Normals: prefer tangent-space; normal map binding and non-sRGB are the primary correctness signals for this cycle.
- Require-normal-map may be configurable (CAD solids often have no normal map — policy must not force maps on every opaque CAD paint unless configured).
- Materials category off by default for CLI; Unreal runs opt in via config.
- Skips never fail the asset; wrong asset class yields no results.

## Strategic Approach

### Solution Direction

Introduce a `materials` rule category and one or two Unreal-only rules that load MaterialInterface assets, read base material properties (domain, blend, shading model, tangent-space flag), and inspect named parameters via MaterialEditingLibrary. Reuse existing registration, dual-host runner, skip semantics, and documentation update path. Keep textures category focused on Texture2D assets; materials own shading/bindings.

High-level flow under Unreal:

```text
AssetRef → load_uobject → MaterialInterface?
         → base Material properties (domain, blend, shading, tangent_space_normal)
         → MaterialEditingLibrary parameter names + scalar/vector/texture values
         → optional Texture2D.srgb check for Normal map
         → RuleResult (info / warning / error) per PBR + normals policy
```

### Key Design Decisions

- New `materials` category (locked direction): PBR/normals are not texture-resolution concerns and are not Unreal path policy; a dedicated category matches existing taxonomy and keeps enablement independent.
- Convention-first PBR (locked direction): Validate named parameters, not material-graph pin tracing. Document that CAD→UE import must expose BaseColor / Metallic / Roughness / Normal (names configurable).
- One vs two rules: Prefer two rules for clarity and independent severity — e.g. `material_is_pbr` and `material_normals_ok` — sharing helpers if needed. Single combined rule is acceptable if REASONS Canvas favors less surface area; either way, both concerns must be coverable by config.
- Configurable parameter names: Defaults match the agreed convention; JSON overrides allow studio-specific parents without code forks.
- Require normal map optional: Default should not error every CAD color material for missing Normal; warn or only error when `require_normal_map: true`, while still erroring on sRGB normal maps when a Normal texture is bound.
- Non-parameterized materials: Emit error (or configurable warning) that required PBR parameters are missing — do not treat as pass.
- Asset applicability: Material and MaterialInstanceConstant (MaterialInterface); StaticMesh slot walking is out of scope unless needed to discover materials — prefer validating material assets discovered by UnrealContext directly.
- Defaults: `categories.materials: false` for CLI; enable in Unreal execute-script config when ready to smoke-test.
- Engine API placement: Follow current precedent — guard + APIs in the materials rule module(s), not growing ValidationContext ABC.

### Alternatives Considered

- Put rules under `textures` or `unreal`: rejected — different asset type and policy; blurs category meaning.
- Validate USD shade networks in CLI this cycle: rejected — user asked for Unreal Python API path; USD can be a later host capability.
- Graph inspection of unparameterized Base Color / Metallic / Roughness pins: rejected for this cycle — fragile in Python and unnecessary if MI convention is enforced.
- Broad materials cleanliness suite (dedupe, usage flags, MI-only): rejected for now — user simplified to PBR + normals.

## Risk & Gap Analysis

### Requirement Ambiguities

- Exact default parameter names and whether BaseColor may be texture-only, vector-only, or either.
- Whether MaterialInstanceDynamic / non-constant instances appear in Content Browser discovery and must be supported.
- Shading-model allowlist: Default Lit only vs also Clear Coat / Subsurface for CAD glass/plastic later.
- Blend-mode allowlist: Opaque-only for v1 vs Opaque+Masked+Translucent with opacity checks.
- Severity when parameters missing vs out of range (always error vs warning for missing Normal).
- Whether to enable `materials` in `scripts/unreal_validate_config.json` in the same cycle as implementation.

### Edge Cases

- Parent Material has parameters; MI overrides none — defaults must still validate as in-range.
- Normal texture bound but asset failed to load → unavailable/error, not silent pass.
- Material (not MI) with parameters — still validate via default parameter getters.
- Non-material assets under content root → empty results, no spam.
- CLI with materials enabled and Unreal absent → skipped results, not run failure.
- CAD materials intentionally without normal maps → must not fail unless `require_normal_map` is on.

### Technical Risks

- MaterialEditingLibrary / MaterialEditor module availability in the editor Python environment used by the execute script — confirm at REASONS/implement time; fall back messaging if library missing.
- Parameter name drift across import versions — mitigate with config lists, not hardcoding only.
- Performance: loading every material and querying parameters on large content roots — acceptable for validation scans; avoid recompile or mutation APIs.
- False confidence: “valid PBR” here means convention compliance in Unreal, not photometric correctness of CAD source.

### Success Criteria Coverage

| # | Description | Addressable? | Gaps/Notes |
|---|-------------|--------------|------------|
| 1 | Materials checks under a materials category | Yes | New `RuleCategory` + package |
| 2 | Unreal-hosted PBR + normals via config | Yes | MaterialEditingLibrary + Material properties |
| 3 | Non-parameterized materials don’t silent-pass | Yes | Missing required param names → error/warn |
| 4 | Skip when Unreal unavailable; no spam on wrong types | Yes | Existing Unreal-only rule pattern |
| 5 | Default CLI unchanged with materials off | Yes | Category default false |
| 6 | Other categories unchanged when materials off | Yes | Discovery only loads enabled categories |
