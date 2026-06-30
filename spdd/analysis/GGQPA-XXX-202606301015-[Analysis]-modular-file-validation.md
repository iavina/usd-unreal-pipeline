# SPDD Analysis: Modular File Validation

## Original Business Requirement

I know what to build a first pass of what the tool might look like. We want to validte all the files in explores against a set of rules. The rules however are modular, meaning I can choose which rules to use or not use, and the system should handle this process smoothly. Because of that, I'm thinking of an abstract class for a rule. The first rules we'd want to build are valid file formats, and file sizes. 
The log should be a structured log that is easily human readable. Because of this, we should also implement the concept of severity in logs, with three levels: info, warning, error. 
The last piece of improtant detail for this, is that the whole system should be configurable. So we need a default configuration, and the ability to input a json configuration file. 

Another small bit, how we can handle a shortcut way to test hard coded values. I'm thinking a local env file that has a hard coded path to a directory I want to use for testing. That way I don't have to point my command uv run pipeline explore [dev-path]  every time.

## Domain Concept Identification

### Existing Concepts (from codebase)

- CLI Application: Typer app in `main.py`, exposed as the `pipeline` console script via `pyproject.toml`.
- Explore Command: Accepts a directory path and prints full paths of immediate child entries; this is the current file-discovery entry point for the pipeline.
- Directory Entry: Filesystem paths discovered from a user-provided directory; these are the likely inputs to validation in this requirement.
- Packaged Python CLI: Project is uv-packaged with hatchling, currently shipping only `main.py` as the installable module.

### New Concepts Required

- Validation Rule: A modular unit of file-checking behavior that can be enabled or disabled independently.
- Rule Set / Rule Registry: The collection of available rules and the mechanism for selecting which rules run for a given execution.
- Validation Run: A single pass over discovered files where selected rules are applied and results are collected.
- Validation Result / Log Entry: A structured, human-readable record of what happened during validation, including severity.
- Log Severity: Classification of validation output into `info`, `warning`, and `error`.
- Pipeline Configuration: System-wide settings controlling enabled rules, rule parameters, and runtime behavior.
- Default Configuration: Built-in baseline settings used when no external configuration is supplied.
- JSON Configuration File: User-supplied configuration that overrides or extends defaults.
- Developer Test Path: A local-only shortcut path loaded from an environment file so repeated manual testing does not require passing a directory argument every time.

### Key Business Rules

- Files discovered through the explore flow are the validation targets for this first pass.
- Rules must be modular: users can choose which rules apply for a run.
- The first concrete rules should cover allowed file formats and file size limits.
- Validation output must be structured, human-readable, and tagged with one of three severities: `info`, `warning`, `error`.
- The system must ship with sensible defaults and also accept a JSON configuration file.
- Local development should support a hard-coded test directory through an environment file to reduce repetitive CLI typing.
- This is a first-pass shape of the tool, not the full long-term USD/Unreal pipeline.

## Strategic Approach

### Solution Direction

- Extend the current CLI-centered pipeline into a small validation workflow built on top of the existing `explore` file-discovery behavior.
- Introduce a modular rule model centered on a shared rule abstraction, with concrete first implementations for file-format validation and file-size validation.
- Separate concerns at a high level into: file discovery, rule selection, rule execution, structured logging, and configuration loading.
- Treat configuration as layered behavior: built-in defaults first, then optional JSON overrides, with a separate local environment shortcut for developer convenience.
- Keep the first slice focused on validating immediate child files from a directory, consistent with the current `explore` behavior, unless a later decision expands scope to recursion.

### Key Design Decisions

- Rule architecture: Use a shared abstract rule concept with pluggable concrete rules → supports modular enable/disable and future rule growth without rewriting the orchestration layer.
- Command shape: Prefer evolving `explore` into “discover + validate” for this slice, or adding a closely related validation command that reuses the same discovery path → keeps the developer workflow simple while avoiding duplicate directory-scanning logic.
- Project structure: Move beyond a single `main.py` file for this feature → the codebase is now large enough that validation, configuration, rules, and logging should not all live in one module, but the first pass should still stay small and understandable.
- Configuration model: Default config in code plus optional JSON file → gives predictable out-of-the-box behavior while allowing project-specific rule selection and thresholds.
- Developer shortcut: Local `.env` file for a default test directory → improves iteration speed, but should remain optional and local-only rather than becoming the primary configuration mechanism.
- Logging model: Structured entries with severity rather than unstructured print statements → creates a foundation for later reporting, CI usage, and human review.
- Incremental scope: Implement only format and size rules in the first pass → defers more complex USD/content validation and Unreal integration to later SPDD cycles.

### Alternatives Considered

- Hard-code two rules directly inside `explore`: rejected because the requirement explicitly calls for modular rule selection and future extensibility.
- Make JSON configuration the only source of truth: rejected because defaults are required and a built-in baseline improves first-run usability.
- Use only CLI flags for enabling rules: rejected as the sole mechanism because the requirement asks for a configurable system with persistent JSON configuration; CLI flags may still be useful later as overrides.
- Require a directory argument on every dev run: rejected in favor of a local environment shortcut for testing ergonomics.

## Risk & Gap Analysis

### Requirement Ambiguities

- “Validate all the files in explores” may mean only immediate child files from `explore`, or eventually recursive validation of nested content.
- It is unclear whether validation should be integrated into `explore` itself or exposed as a separate command that shares discovery logic.
- Allowed file formats are not specified beyond the general idea of valid formats; USD-specific extensions and edge cases need definition.
- File size rules are unspecified: maximum size, per-file vs aggregate limits, and whether limits differ by format.
- The expected behavior for mixed results is unclear: whether warnings should still exit successfully, and whether any `error` severity should fail the command.
- JSON configuration shape is undefined: rule enablement, thresholds, output options, and directory defaults all need a schema decision.
- The environment-file shortcut does not specify variable naming, precedence vs CLI directory argument, or whether it applies only in development.

### Edge Cases

- Directory contains files, subdirectories, hidden files, or unsupported file types.
- A selected rule is enabled in configuration but lacks required parameters.
- JSON configuration file is missing, malformed, or partially invalid.
- `.env` file exists locally but points to a missing directory.
- Both CLI directory input and environment shortcut are present; precedence must be defined.
- A file passes format validation but fails size validation, or vice versa.
- No rules are enabled for a run.
- All discovered entries pass with only informational messages.

### Technical Risks

- Keeping all new behavior in `main.py` will become hard to maintain; this feature likely triggers the project’s first real module extraction.
- Hatchling currently packages only `main.py`; expanding beyond a single-file layout will require packaging updates in `pyproject.toml`.
- `.env` is not currently ignored by git; a local developer shortcut file risks accidental commit unless ignore rules are added.
- Introducing configuration and rule orchestration too early could over-engineer the first pass; the REASONS Canvas should keep the initial implementation narrow.
- Human-readable structured logs need a consistent format early, or later automation and testing will be harder.

### Acceptance Criteria Coverage

| AC# | Description | Addressable? | Gaps/Notes |
|-----|-------------|--------------|------------|
| 1 | Files discovered via explore are validated against selected rules. | Yes | Need to confirm immediate-child scope vs recursive scope. |
| 2 | Rules are modular and can be enabled or disabled. | Yes | REASONS Canvas must define how rule selection is represented in config. |
| 3 | First rules cover valid file formats and file sizes. | Yes | Allowed formats and size thresholds need explicit defaults. |
| 4 | Validation output is structured, human-readable, and severity-tagged. | Yes | Exact log format and fields should be decided in the next phase. |
| 5 | System has default configuration and supports JSON configuration input. | Yes | Config schema and override precedence need definition. |
| 6 | Local development can use an environment file for a default test directory. | Yes | Variable name, precedence, and git-ignore strategy should be decided. |
| 7 | Solution remains extensible for future rules and pipeline behavior. | Yes | First pass should avoid locking the design to only two hard-coded checks. |
