"""Context adapters: filesystem vs Unreal behind one contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pipeline.core.metadata import AssetMetadata


class ValidationContext(ABC):
    """Host-agnostic seam: discover assets and load engine objects when available.

    Unreal-only rules call ``load_uobject``, then use engine APIs themselves.
    Filesystem context returns ``None`` from ``load_uobject`` so those rules skip.
    """

    @abstractmethod
    def get_assets(self) -> list[AssetMetadata]:
        """Return all assets in this context's scope."""

    @abstractmethod
    def get_asset_metadata(self, path: str) -> AssetMetadata | None:
        """Return metadata for one asset path, or None if missing."""

    @abstractmethod
    def load_uobject(self, path: str) -> Any:
        """Filesystem → None. Unreal → EditorAssetLibrary.load_asset result."""
