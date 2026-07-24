"""Unreal editor startup hook (directory on UE_PYTHONPATH).

Registers Content Browser validation menus. Soft-fails so a registration
error never blocks editor startup.
"""

from __future__ import annotations

import unreal

from bootstrap import ensure_repo_on_sys_path

ensure_repo_on_sys_path()

try:
    from register_menus import register_all

    register_all()
except Exception as exc:
    unreal.log_error(f"[Validator] Menu registration failed: {exc}")
