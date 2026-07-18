# SPDD Analysis: Geometry Mesh Closed Rule

## Original Business Requirement

Add a configurable geometry-domain validation rule for mesh closedness, using Unreal DynamicMesh topology queries, so the pipeline can enforce watertight meshes when desired without treating every open border as an unconditional error.

In scope for this cycle:

1. Implement a live geometry rule (working name: `mesh_closed`) under `pipeline/rules/geometry/`, subclassing `GeometryRule`, registered via the existing category-package discovery path.
2. Use Unreal DynamicMesh APIs as the source of topology facts:
   - `get_is_closed_mesh(target_mesh) -> bool` as the primary closedness gate
   - `get_num_open_border_edges(target_mesh) -> int` for diagnostic detail when open
   - `get_num_open_border_loops(target_mesh) -> (count, ambiguous_topology_found)` for hole-loop detail and ambiguity signaling
3. Make closedness **configurable** (e.g. `require_closed`), not an absolute “any open border = error” policy — open meshes are valid for terrain, cloth, planes, intentional holes, etc.
4. On failure (or when reporting open topology), include border-edge and border-loop counts in the message; treat `ambiguous_topology_found` as a warning-worthy signal.
5. Preserve layering: rules must not import `unreal` directly; Unreal-backed mesh facts come through the validation context / host capability surface (same spirit as `size_of`).
6. CLI/filesystem runs remain valid: when mesh topology facts are unavailable, the rule should not hard-crash — emit a non-failing info (or skip) consistent with `file_size`’s “unavailable in this context” pattern.
7. Defaults: keep `categories.geometry` off for default CLI; enable via config (and optionally the Unreal execute-script config) when exercising geometry checks.

Out of scope:

- Full mesh quality suite (non-manifold verts, degenerate tris, normals, UVs, etc.)
- Geometry rules that parse USD/FBX on disk outside Unreal
- Changing host ≠ category model or inventing a second runner
- Unreal editor menu/plugin UI

Success criteria:

- `mesh_closed` is discoverable under the `geometry` category when that category is enabled
- Under Unreal host, closedness can be enforced or relaxed via config
- Open-mesh diagnostics (edge count, loop count, ambiguity) appear in rule messages when relevant
- Rules never call `unreal.*` APIs directly
- Filesystem/CLI runs do not crash when geometry category is enabled without mesh capabilities
- Existing filesystem / unreal_path behavior remains unchanged when geometry stays disabled

## Domain Concept Identification

### Existing Concepts (from codebase)

- Rule Categories: `geometry` exists in `RuleCategory` and config defaults (`categories.geometry: false`) but has only a reserved `GeometryRule` base — no concrete rules yet.
- Validation Context: Shared capability surface (`exists`, `size_of`, `display_of`) with `FilesystemContext` and `UnrealContext`; rules already query context instead of host APIs (`file_size` pattern for unavailable facts).
- Unreal Host: `pipeline/hosts/unreal/` owns `unreal` imports, asset discovery under `/Game/ExampleContent`, and log emission; soft-dependency boundary keeps CLI free of `unreal`.
- Rule Contract: `from_settings` + `applies_to(asset, ctx)` + `validate(asset, ctx)` returning `RuleResult` list; category-package discovery builds enabled rules.
- Precedent rule: `unreal_path` shows thin Unreal-domain checks without importing `unreal` in the rule module (path checks use `AssetRef` only). Mesh closedness needs richer context capabilities than `unreal_path`.

### New Concepts Required

- Mesh Closedness: Whether a mesh has no topological boundary (watertight / closed).
- Open Border Edges: Boundary edges with a single adjacent triangle — count used as diagnostic detail.
- Open Border Loops: Boundary loops (“holes”); may report ambiguous topology.
- Mesh Topology Capability: Context-provided facts (closed flag, border edge count, border loop count, ambiguity) obtained only when the host can build/query a `DynamicMesh`.
- Configurable Closedness Policy: Settings that decide whether open meshes fail, warn, or are allowed, rather than a fixed absolute error.

### Key Business Rules

- Open borders are not always defects; enforcement must be config-driven (`require_closed` or equivalent).
- Primary decision uses closedness (`get_is_closed_mesh`); edge/loop counts enrich messages and support ambiguity warnings.
- `ambiguous_topology_found` should surface as warning-level signal even when policy allows open meshes (or alongside a closedness failure).
- Geometry rules must not import `unreal`; mesh queries stay behind the Unreal host/context boundary.
- When topology cannot be obtained (CLI/filesystem context, non-mesh asset, conversion failure), do not treat as closedness failure by default — report unavailable/skip with info (align with existing unavailable-capability pattern).
- Enabling geometry must not break default CLI runs that leave `categories.geometry` false.

## Strategic Approach

### Solution Direction

Add one concrete `GeometryRule` (`mesh_closed`) that validates through new optional mesh-topology capabilities on `ValidationContext`, implemented by `UnrealContext` via DynamicMesh APIs. Keep filesystem context returning “unavailable.” Configure whether closedness is required and how severely open/ambiguous topology is reported. Reuse existing registration, config defaults, and dual-host runner unchanged.

High-level flow under Unreal:

```text
AssetRef → UnrealContext resolves/loads mesh as DynamicMesh
         → topology facts (closed, border edges, border loops, ambiguity)
         → mesh_closed rule applies require_closed + message detail
```

### Key Design Decisions

- Single rule, not three: One `mesh_closed` rule owns the policy; edge/loop APIs are diagnostics inside its messages (and ambiguity warning), not separate always-on error rules.
- Config-driven closedness (locked direction): `require_closed` (bool) controls whether open meshes fail; severity for open when required should be `error` by default, with optional warning-only mode considered in REASONS Canvas if needed.
- Context capability extension: Prefer adding mesh topology accessors (or one structured “topology facts” method) on `ValidationContext` over leaking `unreal` into `rules/geometry/`.
- Unavailable topology = info, not error: Matches `file_size` unavailable pattern so CLI enabling geometry by mistake stays safe.
- Ambiguity = warning: When `ambiguous_topology_found` is true, emit a warning result (in addition to pass/fail on closedness as configured).
- Asset applicability: Rule should only meaningfully apply to mesh-like Unreal assets; non-mesh assets should skip or report unavailable without failing the run — exact filter (class/path/suffix) deferred to REASONS Canvas.
- Defaults: `categories.geometry: false`; rule defaults enabled when category is on; Unreal smoke config may opt in later without changing CLI defaults.

### Alternatives Considered

- Three separate rules (`mesh_closed`, `border_edges`, `border_loops`): rejected for this cycle — over-splits one topology concern; counts are diagnostics for the closedness policy.
- Unconditional error on any open border: rejected — valid open content is common in real pipelines.
- Rule module imports `unreal` and calls DynamicMesh APIs directly: rejected — breaks host boundary and CLI import isolation.
- Disk-side mesh parsing for CLI: rejected as out of scope; Unreal DynamicMesh is the intended fact source for this slice.

## Risk & Gap Analysis

### Requirement Ambiguities

- Exact Unreal asset → `DynamicMesh` conversion path (static mesh, skeletal mesh, which editor utility APIs) — must be pinned in REASONS Canvas against available stubs.
- Whether `require_closed` alone is enough, or also need `open_severity: error|warning` and `ambiguity_severity`.
- Which assets the rule applies to (all discovered assets vs static meshes only vs path/class filters).
- Whether multiple meshes/components per asset need per-mesh results or one aggregate result.
- Whether geometry should be enabled in `scripts/unreal_validate_config.json` in this cycle or left opt-in via a separate config.

### Edge Cases

- Empty mesh / zero triangles → define closed vs unavailable vs fail.
- Non-mesh assets under the same content root → must not spam false closedness errors.
- Ambiguous topology with `require_closed: false` → still warn.
- Mesh load/conversion failure → info/unavailable, not silent pass-as-closed.
- Filesystem host with geometry enabled → info unavailable for every file if no filter; prefer `applies_to` / capability gate to avoid noise.

### Technical Risks

- DynamicMesh API availability and editor-only constraints — keep all `unreal` usage inside `hosts/unreal`.
- Performance: converting many meshes during a full `/Game/ExampleContent` scan may be slow — REASONS Canvas should keep the capability minimal and avoid redundant conversions where possible.
- Over-growing `ValidationContext` into a god object — add the smallest topology surface needed for this rule only.

### Success Criteria Coverage

| # | Description | Addressable? | Gaps/Notes |
|---|-------------|--------------|------------|
| 1 | `mesh_closed` under geometry category | Yes | First concrete `GeometryRule` |
| 2 | Config-driven closedness via DynamicMesh closed query | Yes | `require_closed` + UnrealContext capability |
| 3 | Edge/loop diagnostics + ambiguity warning | Yes | Message detail + warning result |
| 4 | No `unreal` import in rules | Yes | Context/host boundary |
| 5 | CLI safe when geometry enabled without mesh facts | Yes | Unavailable → info |
| 6 | Default CLI unchanged with geometry off | Yes | Existing defaults |
