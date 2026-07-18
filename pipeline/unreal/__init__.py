"""Unreal Engine host. Imports the engine ``unreal`` module only inside this package."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pipeline.unreal.entry import run_validation as run_validation

__all__ = ["run_validation"]


def __getattr__(name: str) -> Any:
    if name == "run_validation":
        from pipeline.unreal.entry import run_validation

        return run_validation
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
