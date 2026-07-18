"""Normalised asset currency shared by contexts and rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AssetMetadata:
    """Both contexts produce this; all rules consume it."""

    path: str
    name: str
    extension: str
    size_bytes: int = 0
    asset_class: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
