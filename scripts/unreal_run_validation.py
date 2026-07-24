"""UnrealEditor-Cmd / automation entry: run validation once, then let Cmd exit.

Bootstraps from ``__file__``. Used by ``uv run pipeline editor --cmd``.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_STARTUP_DIR = _SCRIPTS_DIR / "startup"
if str(_STARTUP_DIR) not in sys.path:
    sys.path.insert(0, str(_STARTUP_DIR))

from bootstrap import ensure_repo_on_sys_path, purge_pipeline_modules

ensure_repo_on_sys_path(_SCRIPTS_DIR.parent)
purge_pipeline_modules()

from pipeline.unreal import run_validation

_CONFIG = _SCRIPTS_DIR / "unreal_validate_config.json"
ok = run_validation(config_path=_CONFIG)
if not ok:
    sys.exit(1)
