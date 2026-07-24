"""Normalize Content Browser selection paths for the Unreal validation host."""

from __future__ import annotations


def normalize_folder_path(raw: str) -> str:
    """Map Content Browser folder paths to package paths (strip ``/All``)."""
    path = raw.strip().rstrip("/")
    if path.startswith("/All/"):
        path = path[4:]
    elif path == "/All":
        path = "/"
    return path or "/"


def normalize_asset_path(raw: str) -> str:
    """Return an object path suitable for ``UnrealContext.get_asset_metadata``."""
    path = raw.strip()
    if not path:
        return path
    # Already an object path: /Game/Foo/Bar.Bar
    if "." in path.rsplit("/", 1)[-1]:
        return path
    # Package path only: /Game/Foo/Bar → /Game/Foo/Bar.Bar
    name = path.rsplit("/", 1)[-1]
    if name:
        return f"{path}.{name}"
    return path
