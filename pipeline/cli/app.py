"""Typer application and command wiring for the pipeline CLI."""

from pathlib import Path

import typer

from pipeline.config import load_config, load_local_env
from pipeline.logging import render_results
from pipeline.rules import build_rules
from pipeline.validation import discover_files, resolve_directory, validate_files

app = typer.Typer(help="USD Unreal Pipeline project CLI.")


@app.callback()
def main() -> None:
    """USD Unreal Pipeline CLI."""


@app.command()
def explore(
    directory: Path | None = typer.Argument(
        None,
        help="Directory to explore",
    ),
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to JSON config file",
    ),
) -> None:
    """Discover files under a directory and validate them with enabled rules."""
    load_local_env()
    pipeline_config = load_config(config)
    resolved_directory = resolve_directory(directory)
    files = discover_files(resolved_directory)
    rules = build_rules(pipeline_config)

    if not rules:
        typer.echo("WARNING: No validation rules enabled")
        raise typer.Exit(0)

    results = validate_files(files, rules)
    render_results(results, len(files))

    if any(not result.passed for result in results):
        raise typer.Exit(1)

    raise typer.Exit(0)
