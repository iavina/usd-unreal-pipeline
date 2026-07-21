# SPDD Analysis: Shared rule_ignore Path Filtering

## Original Business Requirement

Start a new SPDD cycle (separate from materials PBR/normals) to add a pythonic, gitignore-like ignore mechanism named `rule_ignore` so the pipeline can allow selected assets to go through without being validated by a given rule.

Context from product discussion:

1. Projects contain many assets that must not be judged by domain rules (e.g. fonts, hair, UMG shaders vs CAD PBR materials). Narrowing `content_root` alone is not always enough.
2. The intent is “allowed through the pipeline” in the sense that matched assets are out of scope for the rule — not reported as PBR/policy success, and not failed. Prefer empty / not-applicable behavior over `[SKIPPED]` host-unavailable semantics unless REASONS Canvas decides otherwise.
3. Naming: use `rule_ignore` (snake_case), analogous to `.gitignore` / `.dockerignore`, not “allowlist/denylist” product language.
4. Scope this as a **shared rule framework** feature (like existing `apply_to_extensions`), available to materials and other rules — not a materials-only one-off.
5. Patterns should target asset paths (Unreal Content paths and/or filesystem paths as applicable). Exact pattern dialect (glob vs gitignore syntax, `**` support) is left for REASONS Canvas, with a bias toward familiar ignore-file semantics.

Out of scope for this cycle:

- Changing materials PBR/normals policy itself (domain/shading applicability changes can be a follow-up)
- A mandatory repo-root `.ruleignore` file (optional later; config-driven lists are the first cut unless REASONS prefers a file)
- Reworking host discovery / `content_root`
- Material mutation or import pipeline changes

Success criteria:

- Each rule can declare `rule_ignore` patterns in JSON config (defaults empty)
- Assets whose paths match are not subjected to that rule’s policy checks (do not fail; do not count as policy pass)
- Works consistently with existing `applies_to` / `apply_to_extensions` gating in the runner
- Documented in `RULES.md` alongside shared rule options
- Materials (and other) rules can ignore UI/font/etc. paths without forking per-rule path logic

## Domain Concept Identification

### Existing Concepts (from codebase)

- ValidationRule contract: Shared `apply_to_extensions` and `applies_to(asset, ctx)`; runner skips `validate` when `applies_to` is false (`pipeline/core/runner.py`).
- Shared rule options: Documented in `RULES.md` (`enabled`, `apply_to_extensions`); every concrete rule loads extensions via `normalize_extensions` in `from_settings`.
- AssetMetadata.path: Currency for both filesystem paths and Unreal object paths (`/Game/...`).
- Host ≠ category / content_root: Discovery scope is separate from per-rule applicability; materials already need finer filters inside a wide content tree.
- Skip vs empty results: Unreal-unavailable uses explicit `RuleResult(skipped=True)`; wrong asset type typically returns `[]` (not applicable). Ignore-path semantics should align with one of these deliberately.

### New Concepts Required

- rule_ignore: Per-rule list of path patterns; matches mean the asset is out of scope for that rule.
- Path Pattern Matching: Shared matcher (gitignore-like or glob) applied to `AssetMetadata.path`.
- Out-of-scope Applicability: Distinction between “rule does not apply” (ignore / extension filter) vs “host capability skipped” vs “policy failed/passed”.

### Key Business Rules

- Matched `rule_ignore` → asset proceeds without that rule’s policy (no error from that rule).
- Ignore is not a validation success message; prefer not-applicable (no results) over info spam unless config asks for visibility.
- Empty `rule_ignore` → current behavior (no path ignore).
- Must compose with `apply_to_extensions`: both gates should apply (extensions and ignore).
- Shared implementation on the rule base / shared helper — not copy-pasted into every rule module.
- Naming in config and code: `rule_ignore` (pythonic).

## Strategic Approach

### Solution Direction

Extend the shared rule applicability layer so `rule_ignore` is a first-class per-rule setting, evaluated in `applies_to` (or an equivalent central gate) before `validate`. Provide one shared path-matching utility and wire defaults/`RULES.md`. Materials and other rules then configure ignore patterns in JSON without new category packages.

High-level flow:

```text
asset → applies_to?
          → extension filter (existing)
          → rule_ignore path match? → False (do not validate)
          → else True → validate(...)
```

### Key Design Decisions

- Framework-level feature (locked): Same class of option as `apply_to_extensions`, not materials-only.
- Name `rule_ignore` (locked): Snake_case config key and attribute.
- Gate in `applies_to` (recommended): Runner already respects it; avoids every rule remembering to check ignore lists; keeps `validate` focused on policy.
- Semantics = not applicable (recommended): Matching ignore → `applies_to` false → no `RuleResult` lines (quiet), consistent with extension non-match. Reserve `skipped=True` for host/capability unavailability.
- Pattern dialect: Prefer gitignore-like or `fnmatch`/`**` globs against full `asset.path`; pin exact library/syntax in REASONS Canvas (stdlib-first if possible; avoid new deps unless needed).
- Defaults: `rule_ignore: []` on all rules in defaults (or documented shared option with empty default without necessarily expanding every block if REASONS chooses inheritance from base parsing).
- Optional `.ruleignore` file: Out of scope for v1 unless REASONS finds config-only insufficient; can note as follow-up.

### Alternatives Considered

- Materials-only ignore lists inside PBR/normals rules: rejected as primary approach — user asked for a separate shared cycle and reuse across rules.
- Denylist/allowlist naming: rejected — user prefers `rule_ignore` / gitignore analogy.
- Reporting INFO “[IGNORED]” for every match: rejected as default (noise on large UI trees); optional verbosity can be a later setting.
- Only narrowing `content_root`: insufficient alone when CAD and non-CAD share a tree or discovery root must stay wide.

## Risk & Gap Analysis

### Requirement Ambiguities

- Exact pattern syntax: full gitignore (negation `!`, comments) vs simple glob list.
- Case sensitivity on Windows vs Unreal `/Game` paths.
- Match on full path only vs also `asset.name`.
- Whether category-level shared ignore (one list for all materials rules) is needed in addition to per-rule lists.
- Whether filesystem rules need the same patterns immediately or materials-first wiring with base-class support for all.

### Edge Cases

- Empty pattern list vs missing key → treat as no ignores.
- Pattern that matches everything → rule never runs (config footgun; document).
- Overlap: extension excludes and rule_ignore both false → still no validate.
- Unreal paths with differently normalized slashes or trailing suffixes (`_C` / soft object paths) — normalize before match in REASONS design.
- Negation patterns if gitignore dialect is chosen — define evaluation order.

### Technical Risks

- Pulling a gitignore library vs stdlib `fnmatch` — dependency policy (`uv`, keep deps lean).
- Forgetting to load `rule_ignore` in each rule’s `from_settings` if not centralized — mitigate by base-class helper or shared settings parse used by all rules.
- Behavioral change: silent non-application may surprise operators expecting an ignore audit trail — document clearly; optional later logging.

### Success Criteria Coverage

| # | Description | Addressable? | Gaps/Notes |
|---|-------------|--------------|------------|
| 1 | Per-rule `rule_ignore` in JSON | Yes | Shared option + defaults |
| 2 | Match → no policy fail/pass | Yes | `applies_to` gate → no validate |
| 3 | Composes with `apply_to_extensions` | Yes | Both checked in `applies_to` |
| 4 | Documented in RULES.md | Yes | Shared rule options section |
| 5 | Usable by materials and others | Yes | Framework-level, not materials fork |
