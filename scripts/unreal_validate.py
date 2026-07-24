"""Execute Python Script entry: register Content Browser validation menus.

Menus-only fallback when the editor was not launched with ``UE_PYTHONPATH``
pointing at ``scripts/startup``. Paths come from ``__file__``. Does not run
validation — use the Content Browser menus for that.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_STARTUP_DIR = _SCRIPTS_DIR / "startup"
if str(_STARTUP_DIR) not in sys.path:
    sys.path.insert(0, str(_STARTUP_DIR))

from bootstrap import ensure_repo_on_sys_path

ensure_repo_on_sys_path(_SCRIPTS_DIR.parent)

try:
    from register_menus import register_all

    register_all()
except Exception as exc:
    import unreal

    unreal.log_error(f"[Validator] Menu registration failed: {exc}")
else:
    import unreal

    unreal.log("[Validator] Validation menus ready (use Content Browser right-click).")
