"""Shared Unreal editor bootstrap: sys.path + pipeline module reload."""

from __future__ import annotations

import sys
from pathlib import Path

# scripts/startup/bootstrap.py → repo root is parents[2]
_DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]


def ensure_repo_on_sys_path(repo_root: Path | None = None) -> Path:
    """Insert the repo root on ``sys.path`` so ``import pipeline...`` works."""
    root = (repo_root or _DEFAULT_REPO_ROOT).resolve()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def purge_pipeline_modules() -> None:
    """Drop cached ``pipeline*`` modules so the next import reloads from disk."""
    for name in list(sys.modules):
        if name == "pipeline" or name.startswith("pipeline."):
            del sys.modules[name]
