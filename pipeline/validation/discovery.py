"""Resolve the explore directory and discover validation target files."""

import os
from pathlib import Path

import typer

from pipeline.config import load_local_env

DEV_DIRECTORY_ENV = "PIPELINE_DEV_DIRECTORY"


def resolve_directory(cli_directory: Path | None) -> Path:
    """Resolve the explore directory from CLI input or local environment."""
    load_local_env()

    if cli_directory is not None:
        directory = cli_directory
    elif os.environ.get(DEV_DIRECTORY_ENV):
        directory = Path(os.environ[DEV_DIRECTORY_ENV])
    else:
        raise typer.BadParameter(
            "Directory is required. Provide a path argument or set "
            "PIPELINE_DEV_DIRECTORY in .env"
        )

    if not directory.exists():
        raise typer.BadParameter(f"Directory does not exist: {directory}")
    if not directory.is_dir():
        raise typer.BadParameter(f"Path is not a directory: {directory}")

    return directory


def discover_files(directory: Path) -> list[Path]:
    """Recursively collect all files under a directory in stable sorted order."""
    files = [
        path.resolve()
        for path in sorted(directory.rglob("*"))
        if path.is_file()
    ]
    return files
