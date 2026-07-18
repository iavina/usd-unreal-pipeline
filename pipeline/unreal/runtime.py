"""Shared Unreal import helper for modules that need the engine module object."""

from __future__ import annotations

from pipeline.unreal.env import UNREAL_AVAILABLE, unreal


def import_unreal():
    if not UNREAL_AVAILABLE or unreal is None:
        raise RuntimeError(
            "Unreal host requires the unreal module (run inside the Unreal editor)."
        )
    return unreal
