# SPDD Analysis: Framework Stretch Enhancements

## Original Business Requirement

Extend the modular validator framework with practical stretch capabilities that improve configurability, registration clarity, reporting, and selective rule execution — without Unreal integration, geometry content parsing, or overengineered plugin systems.

In scope for this cycle:

1. Support enabling or disabling categories through configuration
2. Reorganize rules into category packages (replace `builtins/`) with per-category base classes as the source of category identity
3. Use decorator registration bootstrapped by importing category packages, plus `from_settings` on each concrete rule for config→instance construction
4. Add a simple summary report grouped by category
5. Add a mechanism for skipping rules conditionally

Already satisfied (do not re-implement as new work):

- Severity levels on rule results (`info`, `warning`, `error`), including colored warning/error labels in terminal output

Out of scope:

- Unreal integration
- Geometry/texture content validation bodies (packages may exist as reserved structure)
- Full plugin entry-point discovery / package scanning beyond explicit category imports
- Multiple output modes (JSON, etc.) unless needed for the category summary

Success criteria:

- Operators can turn whole domain categories on/off via config without editing code
- Rules live under category folders; category identity comes from the category base class
- Adding a rule means: put it in the right category package, subclass that category base, implement `from_settings` + `validate`, decorate with `@register_rule`, ensure the package imports the module
- Run summary includes category-grouped metrics that are easy to scan
- Rules can be skipped under clear, configurable conditions without burying conditionals in the runner
- Preserve existing layering: execution, rules, config, and reporting stay separated
- Keep the design practical and readable; prefer small extensions over new abstraction layers

## Domain Concept Identification

### Existing Concepts (from codebase)

- Validator Core: CLI `explore` loads config, discovers files, builds rules, runs validation, renders output, sets exit codes.
- Rule Abstraction: `ValidationRule` ABC with `name`, `category`, `enabled`, and `validate`.
- Rule Category Taxonomy: `filesystem`, `geometry`, `textures`, `unreal` as first-class metadata on rules and results.
- Builtin Rules: `file_format`, `file_size`, `file_name` currently under flat `rules/builtins/` with class-level `category = filesystem`.
- Rule Registry Catalog: `RULE_SPECS` table plus per-rule factory helpers in `registry.py`; `build_rules` filters by per-rule `enabled`.
- Configuration: defaults + JSON deep-merge for per-rule settings only (`PipelineConfig.rules`).
- Structured Results: `RuleResult` carries severity, rule, category, message; file pass/fail derived from errors only.
- Reporting: per-file PASS/FAILED blocks with category/severity detail lines; whole-run summary with file/pass/fail/failed-rule counts only (not by category).
- Architecture Docs: `ARCHITECTURE.md` and README explain organization, categories, and how to add rules.

### New Concepts Required

- Category Packages: Rule modules grouped in folders by domain (`filesystem`, `geometry`, `textures`, `unreal`) instead of a flat `builtins/` package.
- Category Base Class: A small per-package base (e.g. `FilesystemRule`) that sets `category` so the folder/domain owns category identity.
- Registration Decorator: `@register_rule` appends rule classes to a registry list when their module is imported.
- Category Import Bootstrap: Explicit imports of category packages (and their rule modules) so decorators actually run; this is the deliberate catalog bootstrap, not silent magic.
- Rule Settings Construction: Each concrete rule provides `from_settings` for config→instance mapping; registry does not own per-rule factories.
- Category Configuration: Config-level enable/disable for domain categories, applied when selecting registered rules.
- Category Summary Report: Aggregated run metrics grouped by category from emitted results.
- Conditional Rule Skip: Extension allow-list style skipping via shared `applies_to` behavior.

### Key Business Rules

- Category disable must prevent rules in that category from running, even if the individual rule is enabled.
- Per-rule `enabled` remains valid; both category and rule gates must pass.
- A rule’s category comes from its category base class (aligned with its package), not from ad-hoc per-check labels.
- Decorator registration only works for imported modules; category package `__init__` (or equivalent) must import concrete rule modules.
- Registry/CLI/runner must not reintroduce per-rule `_build_*` helpers.
- Category summary must be derived from actual `RuleResult` data.
- Conditional skips are config/metadata-driven through a shared gate.
- Severity model already exists; use it in category summaries only.

## Strategic Approach

### Solution Direction

Replace `builtins/` with category packages and category base classes. Register concrete rules with a decorator, bootstrapped by importing category packages. Construct instances with `from_settings`. Gate selection by category and rule enable flags. Add extension-based conditional skip and a category-grouped summary. Keep reserved category packages as structure for later work without implementing geometry/Unreal rule bodies yet (empty or placeholder packages are enough).

### Key Design Decisions

- Category packages (locked): Use `rules/filesystem/`, `rules/geometry/`, `rules/textures/`, `rules/unreal/` instead of `rules/builtins/`.
- Category identity (locked): Per-category base class sets `category` (e.g. `FilesystemRule.category = filesystem`). Concrete rules subclass the local base.
- Registration (locked): `@register_rule` decorator fills an ordered registry list; category package imports are the bootstrap so decorators run. No package scanning.
- Construction (locked): `from_settings` on each concrete rule; registry only filters and calls `from_settings`.
- Category toggles: Top-level `categories` bool map in config, checked during `build_rules`.
- Category summary: After existing totals, show checks/errors/warnings per category that emitted results.
- Conditional skip: Optional `apply_to_extensions`; empty means all files; runner uses `applies_to` before `validate`.

### Alternatives Considered

- Keep `builtins/` + class attribute category only: rejected — folder does not reflect domain categories.
- Derive category by parsing `__module__` strings: rejected as fragile compared to category base classes.
- Explicit class list without decorator: workable but user prefers decorator + category-package bootstrap.
- Full plugin entry-point discovery: rejected as overkill for this cycle.
- Registration decorator without ensuring imports: rejected — would silently miss rules.

## Risk & Gap Analysis

### Requirement Ambiguities

- Exact category config shape (`categories.filesystem: true` vs nested `enabled`) — prefer simple bool map.
- Whether reserved category packages are empty packages with a base class only, or omitted until needed — prefer creating the package + base class now so structure is visible.
- Registration list order: decorator append order follows import order; category `__init__` import order must be documented and stable.

### Edge Cases

- Category disabled but rule enabled → do not run.
- Forgetting to import a new rule module in its category `__init__` → rule silently unregistered; docs must call this out.
- Subclassing the wrong category base while living in another folder → possible inconsistency; mitigate by convention and review (base class is source of truth for category metadata).
- Old JSON without `categories` → defaults keep filesystem on.

### Technical Risks

- Import-cycle risk between registry (defines decorator) and rule modules (import decorator) — keep decorator in a small module or carefully ordered imports.
- Moving modules breaks old import paths — update package exports and docs together.
- Overbuilding reserved packages with fake rules — do not; structure only.

### Success Criteria Coverage

| # | Description | Addressable? | Gaps/Notes |
|---|-------------|--------------|------------|
| 1 | Enable/disable categories via config | Yes | `categories` map + selection gate |
| 2 | Category folders + base classes | Yes | Replace `builtins/` |
| 3 | Decorator registration + import bootstrap | Yes | Document required imports |
| 4 | `from_settings` construction | Yes | No `_build_*` helpers |
| 5 | Severity levels per rule | Already met | Use in category summary |
| 6 | Summary grouped by category | Yes | Extend renderer |
| 7 | Conditional rule skipping | Yes | `apply_to_extensions` |
| 8 | No Unreal / no overengineering | Yes | Reserved packages only |
