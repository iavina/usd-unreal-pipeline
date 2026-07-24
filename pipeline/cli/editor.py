"""Unreal Editor launch CLI command (interactive or Cmd one-shot validate)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import typer

from pipeline.cli.env_util import (
    STARTUP_DIR,
    UE_PYTHONPATH_ENV,
    UNREAL_EDITOR_CMD_ENV,
    UNREAL_EDITOR_ENV,
    UNREAL_PROJECT_ENV,
    UNREAL_RUN_VALIDATION_SCRIPT,
    load_local_env,
)


def _resolve_existing_file(path: Path, kind: str) -> Path:
    resolved = path.expanduser().resolve()
    if not resolved.is_file():
        raise typer.BadParameter(f"{kind} is not a file: {resolved}")
    return resolved


def _resolve_from_option_or_env(
    option: Path | None,
    env_name: str,
    label: str,
) -> Path:
    if option is not None:
        return option
    if os.environ.get(env_name):
        return Path(os.environ[env_name])
    raise typer.BadParameter(
        f"{label} is required. Pass the matching option or set {env_name}."
    )


def _editor_cmd_from_editor(editor: Path) -> Path:
    """Derive UnrealEditor-Cmd next to UnrealEditor when possible."""
    name = editor.name
    if name.lower() == "unrealeditor-cmd.exe":
        return editor
    if name.lower() == "unrealeditor.exe":
        return editor.with_name("UnrealEditor-Cmd.exe")
    if name.lower() == "unrealeditor":
        return editor.with_name("UnrealEditor-Cmd")
    # Fall back: same path (user may have passed Cmd already under another name)
    sibling = editor.with_name("UnrealEditor-Cmd.exe")
    if sibling.is_file():
        return sibling
    return editor


def _child_env_with_pythonpath() -> dict[str, str]:
    child_env = os.environ.copy()
    if not child_env.get(UE_PYTHONPATH_ENV):
        child_env[UE_PYTHONPATH_ENV] = str(STARTUP_DIR.resolve())
        typer.echo(f"Setting {UE_PYTHONPATH_ENV}={child_env[UE_PYTHONPATH_ENV]}")
    else:
        typer.echo(
            f"Keeping existing {UE_PYTHONPATH_ENV}={child_env[UE_PYTHONPATH_ENV]}"
        )
    return child_env


def register(app: typer.Typer) -> None:
    @app.command("editor")
    def editor(
        editor_path: Path | None = typer.Option(
            None,
            "--editor",
            "-e",
            help="Path to UnrealEditor executable "
            f"(or set {UNREAL_EDITOR_ENV}).",
        ),
        project: Path | None = typer.Option(
            None,
            "--project",
            "-p",
            help="Path to .uproject "
            f"(or set {UNREAL_PROJECT_ENV}).",
        ),
        cmd: bool = typer.Option(
            False,
            "--cmd",
            help=(
                "Use UnrealEditor-Cmd: run Unreal validation once and exit "
                "(no interactive menus)."
            ),
        ),
        editor_cmd: Path | None = typer.Option(
            None,
            "--editor-cmd",
            help=(
                "Path to UnrealEditor-Cmd executable for --cmd "
                f"(or set {UNREAL_EDITOR_CMD_ENV}; else derived from --editor)."
            ),
        ),
    ) -> None:
        """Launch Unreal Editor (interactive) or Cmd one-shot validation.

        Interactive: sets UE_PYTHONPATH to scripts/startup when unset so menus
        register on start. UE_PYTHONPATH is the Python startup search path, not
        the editor binary.

        --cmd: runs scripts/unreal_run_validation.py via UnrealEditor-Cmd and
        waits for the process to exit.
        """
        load_local_env()

        project_file = _resolve_existing_file(
            _resolve_from_option_or_env(project, UNREAL_PROJECT_ENV, "Project path"),
            "Project",
        )

        if cmd:
            _run_cmd_validate(
                editor_path=editor_path,
                editor_cmd=editor_cmd,
                project_file=project_file,
            )
            return

        editor_file = _resolve_existing_file(
            _resolve_from_option_or_env(
                editor_path, UNREAL_EDITOR_ENV, "Editor path"
            ),
            "Editor",
        )
        child_env = _child_env_with_pythonpath()
        typer.echo(f"Launching {editor_file} {project_file}")
        try:
            subprocess.Popen(
                [str(editor_file), str(project_file)],
                env=child_env,
                cwd=str(project_file.parent),
            )
        except OSError as exc:
            raise typer.BadParameter(f"Failed to launch editor: {exc}") from exc


def _run_cmd_validate(
    *,
    editor_path: Path | None,
    editor_cmd: Path | None,
    project_file: Path,
) -> None:
    if editor_cmd is not None:
        cmd_path = editor_cmd
    elif os.environ.get(UNREAL_EDITOR_CMD_ENV):
        cmd_path = Path(os.environ[UNREAL_EDITOR_CMD_ENV])
    elif editor_path is not None:
        cmd_path = _editor_cmd_from_editor(editor_path)
    elif os.environ.get(UNREAL_EDITOR_ENV):
        cmd_path = _editor_cmd_from_editor(Path(os.environ[UNREAL_EDITOR_ENV]))
    else:
        raise typer.BadParameter(
            "Cmd executable is required for --cmd. Pass --editor-cmd, --editor, "
            f"or set {UNREAL_EDITOR_CMD_ENV} / {UNREAL_EDITOR_ENV}."
        )

    cmd_file = _resolve_existing_file(cmd_path, "Editor Cmd")
    script = UNREAL_RUN_VALIDATION_SCRIPT.resolve()
    if not script.is_file():
        raise typer.BadParameter(f"Validation script not found: {script}")

    # Cmd exits after ExecutePythonScript by default; no UE_PYTHONPATH needed
    # (script bootstraps from __file__).
    args = [
        str(cmd_file),
        str(project_file),
        f"-ExecutePythonScript={script}",
        "-unattended",
        "-nopause",
    ]
    typer.echo(f"Running Cmd validation: {' '.join(args)}")
    try:
        completed = subprocess.run(
            args,
            cwd=str(project_file.parent),
            check=False,
        )
    except OSError as exc:
        raise typer.BadParameter(f"Failed to launch editor Cmd: {exc}") from exc

    raise typer.Exit(completed.returncode)
