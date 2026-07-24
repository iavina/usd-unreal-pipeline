"""Filesystem validation CLI command."""

from __future__ import annotations

import os
from pathlib import Path

import typer

from pipeline.cli.env_util import DEV_DIRECTORY_ENV, load_local_env
from pipeline.config import ConfigError, load_config
from pipeline.core.filesystem import FilesystemContext
from pipeline.core.runner import validate_assets
from pipeline.report.formatter import format_results
from pipeline.report.styles import ansi as ansi_styles
from pipeline.rules import ValidationRule, build_rules


class DirectoryResolutionError(ValueError):
    """Raised when the validate directory cannot be resolved or is invalid."""


def _resolve_directory(cli_directory: Path | None) -> Path:
    if cli_directory is not None:
        directory = cli_directory
    elif os.environ.get(DEV_DIRECTORY_ENV):
        directory = Path(os.environ[DEV_DIRECTORY_ENV])
    else:
        raise DirectoryResolutionError(
            "Directory is required. Provide a path argument or set "
            f"{DEV_DIRECTORY_ENV} in .env"
        )

    if not directory.exists():
        raise DirectoryResolutionError(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise DirectoryResolutionError(f"Path is not a directory: {directory}")

    return directory


def _rule_names(rules: list[ValidationRule]) -> list[str]:
    return [f"{rule.category.value}/{rule.name}" for rule in rules]


def register(app: typer.Typer) -> None:
    @app.command("validate")
    def validate(
        directory: Path | None = typer.Argument(
            None,
            help="Directory to validate",
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

        try:
            pipeline_config = load_config(config)
            resolved_directory = _resolve_directory(directory)
        except (ConfigError, DirectoryResolutionError) as exc:
            raise typer.BadParameter(str(exc)) from exc

        rules = build_rules(pipeline_config)

        if not rules:
            typer.echo("WARNING: No validation rules enabled")
            raise typer.Exit(0)

        ctx = FilesystemContext(resolved_directory)
        assets = ctx.get_assets()
        results = validate_assets(assets, rules, ctx)
        for line in format_results(
            results,
            len(assets),
            styles=ansi_styles,
            rule_names=_rule_names(rules),
        ):
            typer.echo(line)

        if any(not result.passed for result in results):
            raise typer.Exit(1)

        raise typer.Exit(0)
