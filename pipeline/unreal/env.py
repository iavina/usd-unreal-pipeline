"""Unreal availability boundary — evaluated once at import, then cached.

Importing this module a second time returns the same ``sys.modules`` entry, so
``UNREAL_AVAILABLE`` never flips mid-run.
"""

from __future__ import annotations

try:
    import unreal

    UNREAL_VERSION: str | None = unreal.SystemLibrary.get_engine_version()[:5]
    UNREAL_AVAILABLE: bool = True
except Exception:
    unreal = None  # type: ignore[assignment]
    UNREAL_VERSION = None
    UNREAL_AVAILABLE = False
