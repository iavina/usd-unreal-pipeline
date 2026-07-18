# SPDD Analysis: Validation Context and Unreal Host

## Original Business Requirement

Introduce a dual-host validation model so the same pipeline can run from the existing `uv`/CLI entrypoint and from inside Unreal Engine (editor Python), without hardcoding every rule to behave differently per environment.

In scope for this cycle:

1. Introduce a **runtime Validation Context** that represents *where* validation is running and *how* asset facts are obtained (filesystem vs Unreal), distinct from rule **categories** (`filesystem` / `geometry` / `textures` / `unreal`), which represent *what domain* a check belongs to.
2. Introduce an **asset identity** abstraction (conceptually an `AssetRef`) so the shared validation runner no longer assumes every target is an on-disk `pathlib.Path`.
3. Keep the **validation runner as the shared domain core**: CLI and Unreal are thin hosts that assemble context + asset list + rules, then call the same runner.
4. Rules should depend on **context capabilities** (e.g. size, name, existence, display path) rather than branching on `if host == unreal`.
5. Implement the **Unreal host side** in this cycle (not reserved forever): the project should be runnable via `uv` *and* through Unreal directly. The IDE provides Unreal Python stubs, so design/typing against the `unreal` module is acceptable; runtime import of `unreal` must remain isolated so CLI/`uv` runs still work without Unreal installed.
6. Preserve existing layering: hosts wire the run; validation owns discovery-orchestration/runner/results aggregation; rules own pass/fail; config/reporting stay separate.

Design intent already agreed in discussion (carry forward):

- Host / entrypoint ≠ rule category. Running inside Unreal must not mean “only `rules/unreal/` runs.”
- Context should not become a god object: start with root/scope, identity helpers, and a small IO/capability surface.
- Some rules may remain host-specific by applicability; do not force every rule to be universal.
- Migrate gradually: filesystem context must keep current CLI behavior working; Unreal plugs in as a second host/context.

Out of scope (unless needed as a thin proof for Unreal context):

- Broad geometry/texture content parsing
- Full Unreal content pipeline / asset-import automation
- Rewriting all future naming/convention rules in this cycle
- External plugin marketplaces / entry-point scanning beyond in-repo packaging needed to load under Unreal

Success criteria:

- The same validation core can be invoked from CLI (`uv`) and from an Unreal-hosted entrypoint
- Rules do not contain host-environment conditionals; they ask the context for facts
- Filesystem-hosted runs remain behaviorally equivalent for existing filesystem rules
- Unreal-hosted runs can discover/select targets and obtain facts through an Unreal-backed context
- Host identity and rule category remain separate concepts in design and docs
- `uv` CLI continues to run without requiring Unreal/`unreal` to be importable at process start

## Domain Concept Identification

### Existing Concepts (from codebase)

- CLI Host: Typer `explore` in `pipeline/cli` loads env/config, resolves a directory, discovers files, builds rules, calls the runner, renders results, sets exit codes — the only current entrypoint.
- Validation Runner: `pipeline/validation/runner.validate_files` loops files × rules with `applies_to` / `validate`; no rule logic inside.
- On-disk Discovery: `resolve_directory` + `discover_files` produce sorted `list[Path]` from a filesystem root (CLI arg or `PIPELINE_DEV_DIRECTORY`).
- Rule Contract: `ValidationRule` ABC with `from_settings`, `applies_to(file: Path)`, `validate(file: Path)` — tightly coupled to `pathlib.Path` and disk semantics (`suffix`, `stat()` in concrete rules).
- Rule Categories: Domain packages `filesystem` / `geometry` / `textures` / `unreal` with category base classes; `unreal` is currently reserved (base class + package only, no concrete registered rules).
- Rule Registry: Category-package discovery + `build_rules(config)` gated by category/rule enable flags.
- Config / Results / Reporting: JSON-merged defaults; `RuleResult` + `FileValidationResult`; Rich terminal rendering. Result aggregation today keys display off `Path`.
- Explicit prior deferral: Architecture/docs and prior SPDD cycles treated Unreal Engine integration as out of scope; reserved `rules/unreal/` was structural only.

### New Concepts Required

- Host / Entrypoint: Who starts the process — CLI via `uv`, or Unreal editor Python — thin adapters only.
- Validation Context: Runtime capability surface for obtaining asset facts and host metadata; filesystem-backed and Unreal-backed variants.
- Asset Reference: Stable per-run identity + display form for one validation target (OS path vs Unreal object path / package path), without embedding IO.
- Shared Validation Invocation: Generalized “validate assets with rules under a context” flow that both hosts call (evolution of today’s runner).
- Unreal Host Adapter: Editor-side entry that builds un Unreal context, obtains an asset list, loads config/rules, runs the shared core, and surfaces results appropriately for that host.
- Capability-Oriented Rule Access: Rules read size/name/existence (and similar) through the context instead of calling `Path` APIs directly.
- Soft Unreal Dependency Boundary: `unreal` module used only behind the Unreal host/context boundary so CLI packaging stays independent.

### Key Business Rules

- Host must not be conflated with rule category: Unreal host may still run filesystem/geometry/textures rules when those rules’ capabilities are satisfiable.
- Rules must not branch on host kind for core checks; host-specific applicability is expressed by whether a rule can be satisfied / selected, not by scattered `if unreal` inside rule bodies.
- CLI/`uv` must remain usable without Unreal installed or importable.
- Filesystem context must preserve current explore→discover→validate behavior for existing rules after the abstraction lands.
- Unreal context must speak Unreal path/asset conventions for identity/display while exposing the same conceptual capabilities rules already need.
- Discovery belongs to the host/context boundary (how targets are found), not inside individual rules.
- Runner remains free of per-rule and per-host special cases beyond applying rules to assets through the shared contract.

## Strategic Approach

### Solution Direction

Evolve the existing layered validator rather than replacing it. Insert an asset-reference + validation-context seam between hosts and rules; generalize the runner to operate on assets + context; keep the CLI as the filesystem host; add an Unreal host that uses an Unreal-backed context and the same rule/config/result pipeline. Treat Unreal Python as an optional runtime available inside the editor (stubs for authoring), isolated behind the Unreal adapter so `uv` runs stay clean.

High-level flow:

```text
Host (CLI | Unreal)
  → load config / build rules
  → build ValidationContext
  → discover/select AssetRefs
  → shared runner (assets × rules via context capabilities)
  → host-appropriate result presentation
```

### Key Design Decisions

- Host vs category (locked): Runtime context/host is orthogonal to `RuleCategory`. Docs and naming must keep them distinct (`unreal` category ≠ “running in Unreal”).
- Shared core (locked): Validation runner remains the domain execution layer both hosts call; hosts do not reimplement rule loops.
- Capability-oriented rules (locked): Rules ask context for facts (size, name, existence, display identity) instead of assuming `Path.stat()` / OS paths everywhere.
- Dual implementation of context: Filesystem context wraps current disk discovery/IO; Unreal context wraps editor/asset APIs behind the same conceptual surface.
- Soft `unreal` import boundary: Only Unreal host/context modules import `unreal`; CLI path must not import them at startup.
- Incremental migration: Introduce the seam and migrate existing filesystem rules onto context capabilities; Unreal host lands in the same cycle as a real second entry, not a placeholder package alone.
- First Unreal proof should be real but thin: enough to demonstrate discovery/selection + context-backed facts + shared runner invocation inside Unreal; deep Unreal content rules can follow once the seam exists.
- Context size discipline: Prefer a small capability surface over a kitchen-sink context object.

### Alternatives Considered

- Keep `Path` everywhere and special-case Unreal only in `rules/unreal/`: rejected — forces host branching and blocks reusing filesystem-capable checks under Unreal when facts are available.
- Pass a host enum into every rule (`if context == unreal`): rejected — recreates the coupling the context is meant to remove.
- Separate Unreal-only validator codebase: rejected — duplicates runner/config/reporting and breaks the modular goal.
- Delay Unreal host until after a long filesystem-only abstraction cycle: rejected by product intent — user is ready to start Unreal work now; seam and Unreal host belong together so the abstraction is proven by a second host.
- Make Context own rule selection policy heavily: rejected for this cycle — keep selection mostly config + `applies_to`; context supplies capabilities and identity.

## Risk & Gap Analysis

### Requirement Ambiguities

- Exact first Unreal entry UX: editor menu command vs console Python invoke vs both — needs a concrete choice in REASONS Canvas.
- Unreal discovery scope for v1: selected assets, a content folder/path, asset-registry query, or a filesystem path under the project Content directory — not specified yet.
- Which existing filesystem rules must work unchanged under UnrealContext in v1 versus remaining filesystem-host-only until capabilities exist (e.g. byte size via Unreal APIs may differ from `Path.stat()`).
- How results are presented inside Unreal (reuse Rich terminal logging vs Unreal log / dialog) — host-appropriate presentation is required, depth TBD.
- How the package is loaded on Unreal’s Python path (editable install, Content/Python, `sys.path` bootstrap) — operational detail for REASONS Canvas / Safeguards.
- Whether this cycle includes one concrete `UnrealRule` body, or only host+context+discovery proof with category package still thin — user wants Unreal work now; prefer at least one thin end-to-end Unreal-hosted validation path; a first unreal-domain rule is optional if host proof is otherwise complete.

### Edge Cases

- CLI run where someone accidentally imports Unreal modules → must not crash if `unreal` is missing.
- Unreal run where filesystem-only capabilities are requested by a rule that was not filtered out → need a clear failure/skip policy (skip vs error vs host filtering).
- Mixed identity display in logs (OS path vs `/Game/...`) — renderer should use asset display identity from the ref/context.
- Empty Unreal selection / no discoverable assets → same class of “nothing to validate” behavior as empty directory, with clean messaging.
- Config loading from Unreal host (cwd may not be repo root) — path resolution for `--config` / defaults needs an explicit Unreal-host strategy.

### Technical Risks

- `pathlib.Path` leakage: current rule contract and result model are Path-centric; incomplete migration will leave half the stack assuming disk.
- Unreal API surface mismatch: stubs help typing, but editor version differences may change asset registry / package path APIs — keep Unreal context boundary small and swappable.
- Overbuilding Context into a god object — mitigate by starting with the minimal capability set existing rules need, plus identity/display.
- Packaging friction under Unreal Python — if the host cannot import `pipeline`, the dual-host goal fails regardless of abstractions; treat loadability as a first-class safeguard.
- Naming collision in docs (`unreal` category vs Unreal host) — architecture note must explicitly separate them to avoid contributor confusion.

### Success Criteria Coverage

| # | Description | Addressable? | Gaps/Notes |
|---|-------------|--------------|------------|
| 1 | Shared validation core callable from CLI and Unreal | Yes | Generalize runner; add Unreal host adapter |
| 2 | Rules use context capabilities, not host branching | Yes | Migrate rule contract off raw Path IO |
| 3 | Filesystem/`uv` behavior preserved | Yes | FilesystemContext + CLI host keep current flow |
| 4 | Unreal-hosted discover/select + fact access | Yes | Needs concrete discovery UX decision in canvas |
| 5 | Host ≠ rule category | Yes | Naming/docs + selection model |
| 6 | CLI works without `unreal` importable | Yes | Soft dependency boundary |
| 7 | Thin but real Unreal integration this cycle | Partial | Entry + context required; first UnrealRule optional if E2E host proof is otherwise solid |
