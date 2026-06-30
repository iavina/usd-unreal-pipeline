# Agent Guidance

## Project Workflow

Use Structured Prompt-Driven Development (SPDD) for meaningful project changes. SPDD is the default workflow for features, larger refactors, behavior changes, and work where requirements or architecture need to stay traceable.

Follow the project SPDD skill when SPDD is relevant:

- Read `.cursor/skills/spdd/SKILL.md`.
- Use the existing `/spdd-*` Cursor commands for the actual workflow.
- Treat `spdd/analysis/` and `spdd/prompt/` files as version-controlled design artifacts.
- Keep structured prompts and implementation code synchronized.

For small mechanical edits, direct implementation is fine. For non-trivial work, prefer:

1. `/spdd-analysis` from the business requirement.
2. `/spdd-reasons-canvas` from the analysis.
3. Human review of the REASONS Canvas.
4. `/spdd-generate` from the approved prompt.
5. `/spdd-prompt-update` or `/spdd-sync` when intent or code changes.

## Python Tooling

- Use `uv` for Python dependency management and command execution.
- Use Typer for CLI code.
- Prefer `uv run ...` when running project Python commands.
- Add runtime dependencies through `uv add ...` when possible.

