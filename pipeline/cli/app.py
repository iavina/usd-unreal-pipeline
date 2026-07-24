"""Typer application wiring for the pipeline CLI."""

from __future__ import annotations

import typer

from pipeline.cli import editor as editor_cmd
from pipeline.cli import validate as validate_cmd

app = typer.Typer(help="USD Unreal Pipeline project CLI.")


@app.callback()
def main() -> None:
    """USD Unreal Pipeline CLI."""


validate_cmd.register(app)
editor_cmd.register(app)
