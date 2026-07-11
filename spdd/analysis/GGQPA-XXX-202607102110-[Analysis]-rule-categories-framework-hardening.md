# SPDD Analysis: Rule Categories and Framework Hardening

## Original Business Requirement

Harden the existing filesystem validator into a modular framework that can grow cleanly before starting geometry content rules.

Agreed scope for this SPDD cycle:

1. Rule categories as first-class metadata, modeled as **domain/context groupings** (not per-check type splits like format vs size)
2. Structured output includes category and severity on each rule result
3. Clearer registration / grouping so rules are organized beyond a flat hand-wired list
4. One small new filesystem rule (or equivalent) to prove the framework scales with minimal core changes
5. README architecture / how-to-extend note covering: how the framework is organized, how rules are added, how categories or registration work, and how to run the validator

Locked category taxonomy (domain/context):

- `filesystem` (also thinkable as OS/host checks): path, name, size, extension, and similar on-disk rules — all current rules live here
- `geometry`: mesh quality checks (manifold, winding, …) — reserved for a later cycle
- `textures`: texture/image asset checks — reserved for later
- `unreal`: engine/context checks — reserved for a later integration stage

Categories answer *which validation domain/context a rule belongs to*. Individual rules answer *which specific check runs inside that domain*.

Explicitly deferred to a later cycle:

- Geometry content validation (manifold checks, winding-order consistency)
- Unreal integration
- Mesh/USD content parsing beyond filesystem metadata
- Implementing live rules under `geometry`, `textures`, or `unreal`

Project success criteria for this cycle:

- Separate execution, rules, configuration, and reporting clearly
- Support multiple rules in a reusable structure
- Organize rules by domain/context categories that can scale
- Preserve readable, structured output with rule metadata (file/target, rule name, category, status/severity, message)
- Configurable behavior separated from rule bodies
- Make it easy to add another rule with minimal core changes
- README or architecture note explaining organization, rule addition, categories/registration, and how to run
- Demonstrate that the framework can be extended cleanly
- Remain filesystem-based for this cycle; do not use Unreal; do not collapse rule logic into one script; do not overengineer

## Domain Concept Identification

### Existing Concepts (from codebase)

- Validator Core / Execution Flow: CLI `explore` coordinates env/config load, discovery, rule building, validation run, rendering, and exit codes — without owning rule logic.
- ValidationRule Abstraction: ABC contract (`name`, `enabled`, `validate`) that concrete rules implement as independent units.
- Concrete Rules: `FileFormatRule` and `FileSizeRule` under `rules/builtins/`, configured via defaults/JSON thresholds and enable flags.
- Rule Registry: `build_rules` selects and instantiates enabled rules from config; currently a flat, hand-maintained list of imports and `if` blocks.
- Validation Results: `Severity`, `RuleResult` (severity, rule, message), and `FileValidationResult` (file + aggregated rule results, pass derived from absence of errors).
- Structured Reporting: Logging renderer prints per-file PASS/FAILED blocks, indented rule lines, and a run summary; consumes validation models without owning them.
- Configuration: `DEFAULT_CONFIG` plus optional JSON merge; per-rule settings live outside rule bodies.
- Package Layering: Domains already separated into `cli`, `config`, `rules`, `validation`, and `logging`.
- Developer Docs: README covers setup/run/config at a usage level; SPDD prompts hold internal design history but are not a complete architecture/extension guide.

### New Concepts Required

- Rule Category (domain/context): A first-class label for the validation domain a rule belongs to — e.g. `filesystem`, `geometry`, `textures`, `unreal` — carried on rules and into results/output. Distinct from rule identity (`file_format`, `file_size`).
- Category Taxonomy: The agreed set of domain categories the framework recognizes now, including reserved categories that have no live rules yet so future Unreal/geometry work has a clear home.
- Category-Aware Registration: A clearer registration/grouping pattern that associates each rule with a domain category and reduces core churn when adding rules, without becoming a plugin megasystem.
- Result Metadata Completeness: Extending structured results/output so each applied check communicates file, rule name, category, severity/status, and message.
- Extension Evidence Rule: One additional small rule under `filesystem` that demonstrates adding a rule with minimal core changes (proves scale without inventing a fake second “live” domain).
- Architecture Note: User-facing documentation describing framework organization, domain categories, how to add rules, how registration works, and how to run.

### Key Business Rules

- Categories are domain/context groupings (`filesystem`, `geometry`, `textures`, `unreal`), not cosmetic splits of individual check types (`format` vs `size`).
- Multiple rules may share one category; category ≠ one-rule-per-category.
- Categories must appear on rules and in structured output so grouping is real metadata, not folder names alone.
- Reserved categories may exist in the taxonomy/docs/registry shape before they have implementations.
- Severity remains part of each rule result and must be visible in structured output, not only stored in the model.
- Warnings must not fail a file; only errors fail (existing invariant).
- Configuration (enablement, thresholds, patterns) stays outside rule bodies.
- Adding a new rule should not require rewriting the validator core or collapsing logic into the runner/CLI.
- This cycle stays filesystem-based: implement live rules only under `filesystem`; do not implement Unreal or mesh/geometry content parsing yet.
- Prefer clarity and practical pipeline structure over clever abstraction.

## Strategic Approach

### Solution Direction

Evolve the existing layered validator rather than replacing it. Introduce domain/context rule categories as shared metadata on the rule contract and on each `RuleResult`, update reporting to surface category and severity, tighten registration so rules are declared with their domain category rather than ad-hoc `if` blocks, add one small additional `filesystem` rule as extension proof, document the category taxonomy (including reserved `geometry` / `textures` / `unreal`) in the README, and keep geometry/Unreal rule bodies out of this cycle.

High-level flow remains: CLI → config → discovery → category-aware rule selection → runner → structured render → exit code.

### Key Design Decisions

- Category model: Lock categories as domain/context labels — `filesystem`, `geometry`, `textures`, `unreal` — with all current and the new extension rule under `filesystem` → recommended because it matches the pipeline’s future (OS vs Unreal, geometry vs textures) and avoids weak per-check categories.
- Taxonomy vs live population: Treat the framework’s recognized taxonomy (at least `filesystem` plus reserved domains such as `geometry`) as the grouping system, with registration/docs making reserved categories real structure. Live rules can remain concentrated in `filesystem` while this cycle stays filesystem-only → recommended over inventing artificial live categories like `format`/`size`.
- Registration style: Prefer a small declarative registry map / registration table that records rule identity + category over automatic plugin discovery → recommended for clarity without overengineering.
- Structured output enrichment: Include category and severity in each per-rule detail line while keeping the existing PASS/FAILED file summary and run summary → recommended so operators can see full result metadata.
- Extension proof rule: Add one simple filesystem rule (candidate families: naming/pattern, empty-file, or path-depth) still categorized as `filesystem` → recommended to prove scale without pretending it is geometry.
- Documentation home: Expand README with architecture, domain category taxonomy, add-a-rule steps, and run instructions → recommended so contributors can extend the framework without reading SPDD history.
- Category enable/disable in config: Optional; per-rule enable already exists → defer unless trivial, to keep this cycle focused.

### Alternatives Considered

- Per-check categories (`format`, `size`, `naming`): rejected after clarification — too fine-grained and misaligned with application/domain contexts the pipeline is heading toward.
- Folder-only categories without result metadata: rejected because folders alone do not put category into structured output.
- Auto-discovery / plugin loading of rule modules: rejected for this cycle as more clever than needed.
- Implementing live `geometry` or `unreal` rules now: deferred; mesh parsing and Unreal belong to later cycles.
- Full rewrite of the validator core: rejected; current layering already separates execution, rules, config, and reporting — harden rather than replace.

## Risk & Gap Analysis

### Requirement Ambiguities

- Whether reserved categories (`geometry`, `textures`, `unreal`) are represented only in docs/enum/taxonomy, or also as empty registry slots / package placeholders — REASONS Canvas should pick the lightest clear option.
- The specific third `filesystem` rule is not chosen yet; REASONS Canvas should pick one concrete rule.
- Whether to name the host/OS domain `filesystem` or `os` — lean `filesystem` for clarity with current checks; document that it is the OS/host side versus future `unreal`.
- How densely severity/category should appear in terminal lines (they must be clearly communicated in structured output).

### Edge Cases

- A rule emits results whose category disagrees with the rule’s declared category — single source of truth must be the rule’s category.
- Someone later adds a geometry rule but forgets to use the `geometry` category — docs and registry pattern should make the correct choice obvious.
- Config enables a rule but omits new settings for the third rule — defaults must cover it.
- Mixed severities on one file (info + warning + error) — output must remain readable; pass/fail still driven by errors only.
- Existing JSON configs without category-related keys must keep working.
- README drift if architecture text describes a registration pattern the code does not match.

### Technical Risks

- Touching `RuleResult` and the rule ABC will ripple through builtins, registry, and renderer — keep the change additive and small.
- Overbuilding registration (decorators, entry points, dynamic imports) could hurt clarity.
- If reserved categories are invisible in code, the framework may still look like a flat filesystem-only list — mitigate by encoding the taxonomy in a shared category concept, not only prose.
- Skipping the architecture note or the third rule would weaken the extensibility story this cycle is meant to prove.

### Success Criteria Coverage

| # | Description | Addressable? | Gaps/Notes |
|---|-------------|--------------|------------|
| 1 | Separate execution, rules, configuration, and reporting | Yes | Already largely true; preserve while adding category/registration |
| 2 | Multiple rules in a reusable structure | Yes | Two exist; add one more under `filesystem` as extension proof |
| 3 | Domain/context rule categories that can scale | Yes | Taxonomy (`filesystem` + reserved `geometry`/`textures`/`unreal`); not format/size splits |
| 4 | Rule abstraction / registration pattern | Yes | Strengthen registry with rule + category declaration |
| 5 | Structured output with file, rule, category, severity, message | Partial → Yes | Add domain category; surface severity in output |
| 6 | Configurable behavior outside rule bodies | Yes | Keep/extend defaults + JSON; configure the new rule the same way |
| 7 | README / architecture note (org, add rules, categories, run) | Partial → Yes | Document domain taxonomy and reserved categories |
| 8 | Framework extends cleanly | Partial → Yes | Third `filesystem` rule + docs; geometry left as next extension path |
| 9 | Filesystem-only this cycle; no Unreal; no overengineering | Yes | Live rules only under `filesystem`; reserved domains documented, not implemented |
