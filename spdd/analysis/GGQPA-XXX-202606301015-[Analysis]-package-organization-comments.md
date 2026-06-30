# SPDD Analysis: Package Organization and Comments

## Original Business Requirement

I want to organize the pipeline module better. Every file is in the root, and the rules folder also has every rule and the base class in the root. Also, there's a clear lack of comments and structure for humans to read. It sounds to me like we already have clear domains: logging, rules, config, cli. 
Also, coming from other programming languages, having a base.py file with a class inside feels so weird, shouldn't the file be named after the class with capitalization? Or is python convention just different?
As for the comments, we don't need to comment every single function, keep comments minimal but helpful; also adding top level file comments to quickly understand what this file contains if not immediately obvious at a glance.

## Domain Concept Identification

### Existing Concepts (from codebase)

- CLI Domain: `pipeline/cli.py` owns the Typer app and the `explore` command orchestration.
- Configuration Domain: `pipeline/config.py` owns default configuration, JSON merging, and `PipelineConfig`.
- Environment Domain: `pipeline/env.py` loads local `.env` values for development variables.
- Discovery Domain: `pipeline/discovery.py` resolves the target directory and recursively discovers files.
- Validation Domain: `pipeline/validation.py` applies rules and aggregates per-file validation results.
- Logging Domain: `pipeline/log_entry.py` defines log/result data objects and `pipeline/log_renderer.py` renders human-readable output.
- Rules Domain: `pipeline/rules/` contains the rule abstraction, concrete file format and size rules, and rule registry.
- Packaging Boundary: `pyproject.toml` packages the `pipeline` package and exposes `pipeline.cli:app`.

### New Concepts Required

- Package Organization Convention: A project-level convention for how domains map to folders and modules.
- Human Readability Layer: Minimal comments, docstrings, and module-level context that help readers orient without creating comment noise.
- Rule Type Organization: A clearer structure for rule interfaces, concrete rule implementations, and rule registration.
- Python Naming Decision: Explicit adoption of Python module naming conventions so class names and file names feel intentional rather than accidental.

### Key Business Rules

- Organize by domain boundaries already visible in the codebase: `cli`, `config`, `logging`, `rules`, and supporting validation/discovery behavior.
- Prefer Python conventions for module names: lowercase `snake_case` file names, not capitalized class-style file names.
- Do not create one file per class just to mirror other languages; use modules as cohesive units of related behavior.
- Improve human readability with minimal, useful module-level comments or docstrings where the file purpose is not obvious.
- Avoid commenting every function or restating obvious implementation details.
- Preserve current CLI behavior while reorganizing.

## Strategic Approach

### Solution Direction

- Refactor the package structure around stable domains rather than around individual classes.
- Keep Python naming idiomatic: modules and packages should be lowercase, usually `snake_case`; classes remain `PascalCase`.
- Move logging-related data and rendering into a dedicated logging package, rule abstractions and concrete rules into clearer rule subpackages or modules, and keep CLI/config boundaries explicit.
- Treat comments as navigation aids: add short module docstrings at the top of files whose role is not obvious, and add inline comments only for non-obvious design choices.
- Keep the refactor behavior-preserving: this should be mostly structure, imports, and documentation, not new validation behavior.

### Key Design Decisions

- Python file naming: Use lowercase module names like `base.py`, `file_format.py`, and `file_size.py`; this is Python convention from PEP 8. A file named `ValidationRule.py` would feel natural in Java/C#-style ecosystems, but it is not idiomatic Python.
- `base.py` question: `base.py` is acceptable in Python when it holds base abstractions for a package, but a more descriptive name like `rule.py` or `validation_rule.py` may be clearer if the package grows.
- Domain package shape: Prefer domain folders when a domain has multiple responsibilities. For example, logging may deserve `pipeline/logging/` because it has data models and rendering; rules may deserve substructure because it has base contract, implementations, and registry.
- CLI stability: Keep the external command `pipeline explore` unchanged while internal modules move.
- Comments: Use module docstrings for orientation, not large block comments. For example, a top-of-file docstring can say that `pipeline/logging/rendering.py` formats validation results for terminal output.

### Alternatives Considered

- Keep the current flat package: rejected because the codebase already has enough domains that root-level files are becoming harder to scan.
- Rename every file to match its primary class with capitalization: rejected because it conflicts with Python convention and would make imports less idiomatic.
- Put every class in its own file: rejected because Python modules commonly group small related functions/classes, and one-class-per-file can create unnecessary navigation overhead.
- Add extensive comments to every function: rejected because it adds noise and increases maintenance burden.

## Risk & Gap Analysis

### Requirement Ambiguities

- Exact target folder structure is not specified; the REASONS Canvas should propose a concrete structure for review.
- It is unclear whether `discovery` and `validation` should remain root-level domains or become part of broader `explore` or `validation` packages.
- The desired amount of top-level file commentary needs a concrete convention: module docstrings vs comments, and which files require them.
- Rule organization could be shallow (`rules/base.py`, `rules/file_format.py`) or deeper (`rules/core.py`, `rules/builtins/file_format.py`).

### Edge Cases

- Moving modules may break imports if package paths are not updated consistently.
- Packaging may fail if `pyproject.toml` package inclusion no longer matches the new layout.
- SPDD prompt files may reference old module paths after the refactor.
- Over-organizing too early could create too many folders for a small codebase.
- Top-level docstrings may become stale if they describe details rather than the file's stable responsibility.

### Technical Risks

- This is a behavior-preserving refactor, so tests or CLI smoke checks are important to prove `pipeline explore` still works.
- The existing implementation has no automated tests yet, so validation will rely on CLI smoke tests unless tests are introduced in the same or a later SPDD slice.
- Import churn can obscure whether behavior changed; the REASONS Canvas should make safeguards explicit: no behavior changes, no config format changes, and no command changes.

### Acceptance Criteria Coverage

| AC# | Description | Addressable? | Gaps/Notes |
|-----|-------------|--------------|------------|
| 1 | Organize `pipeline` into clearer domain modules/packages. | Yes | Canvas should choose the exact folder layout. |
| 2 | Improve `rules` organization beyond a flat folder. | Yes | Need to choose between shallow rename and deeper `builtins`/`core` grouping. |
| 3 | Explain and apply Python naming conventions. | Yes | Adopt lowercase module names and PascalCase classes. |
| 4 | Add minimal helpful comments or top-level file context. | Yes | Canvas should define when to use module docstrings. |
| 5 | Preserve current CLI behavior. | Yes | Requires smoke test after refactor. |
| 6 | Avoid noisy comments on every function. | Yes | Safeguards should explicitly forbid redundant comments. |

