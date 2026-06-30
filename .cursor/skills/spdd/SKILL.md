---
name: spdd
description: Guides Structured Prompt-Driven Development using REASONS Canvas prompts. Use when the user mentions SPDD, structured prompts, REASONS, openspdd, spdd analysis, prompt generation, prompt sync, or asks to implement features through the project SPDD workflow.
---

# SPDD

## Purpose

Use Structured Prompt-Driven Development to keep intent, design, implementation, and later changes connected through version-controlled prompt artifacts.

For this project, SPDD is a workflow concept and engineering discipline. The actual implementation workflow should use the existing project SPDD tooling and Cursor commands, not a hand-rolled replacement.

## Core Idea

SPDD treats the structured prompt as a maintained project artifact, not as disposable chat text. The prompt captures the "why", "what", "how", constraints, and implementation sequence before code is generated.

The project uses the REASONS Canvas:

- `R - Requirements`: goal, scope, value, definition of done.
- `E - Entities`: domain concepts, relationships, data flow.
- `A - Approach`: strategy, trade-offs, architecture direction.
- `S - Structure`: components, layering, dependencies.
- `O - Operations`: ordered, executable implementation tasks.
- `N - Norms`: coding standards and project conventions.
- `S - Safeguards`: non-negotiable constraints and checks.

## Workflow

1. Start from business requirements, not code.
2. Run analysis to ground the requirement in the current codebase.
3. Generate a REASONS Canvas prompt and review it before implementation.
4. Implement from the approved prompt, following `Operations` in order.
5. Validate behavior against `Requirements`, `Norms`, and `Safeguards`.
6. When requirements or code change, update or sync the structured prompt so it remains true.

Use the existing commands when they fit:

- `/spdd-analysis`: business requirement plus targeted codebase exploration to produce enriched context.
- `/spdd-reasons-canvas`: generate an implementation-ready REASONS Canvas prompt.
- `/spdd-generate`: generate or update implementation from an approved structured prompt.
- `/spdd-prompt-update`: change an existing prompt when intent or architecture changes.
- `/spdd-sync`: update the prompt after implementation changes so prompt and code stay aligned.

## Operating Rules

- Do not jump straight from a feature request to implementation when SPDD is appropriate.
- Do not implement from an unreviewed or incomplete REASONS Canvas for non-trivial work.
- Fix the prompt first when the code reveals a missed requirement, wrong abstraction, or changed constraint.
- Keep prompt changes and related code changes together when possible.
- Explore codebase context narrowly and conceptually during analysis; avoid reading the whole repo by default.
- Prefer existing project patterns and `uv` for Python dependency and command execution.

## Python Project Defaults

- Use `uv` for Python environment, dependency, lockfile, and command execution workflows.
- Use Typer for CLI entry points.
- Prefer running project commands through `uv run`.
- If exposing a packaged command, add a `[project.scripts]` entry in `pyproject.toml`.

