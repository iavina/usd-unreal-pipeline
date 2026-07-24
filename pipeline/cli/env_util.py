"""Shared CLI environment helpers."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

DEV_DIRECTORY_ENV = "PIPELINE_DEV_DIRECTORY"
UNREAL_EDITOR_ENV = "PIPELINE_UNREAL_EDITOR"
UNREAL_EDITOR_CMD_ENV = "PIPELINE_UNREAL_EDITOR_CMD"
UNREAL_PROJECT_ENV = "PIPELINE_UNREAL_PROJECT"
UE_PYTHONPATH_ENV = "UE_PYTHONPATH"

# pipeline/cli/env_util.py → repo root is parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]
STARTUP_DIR = REPO_ROOT / "scripts" / "startup"
UNREAL_RUN_VALIDATION_SCRIPT = REPO_ROOT / "scripts" / "unreal_run_validation.py"


def load_local_env() -> None:
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)
