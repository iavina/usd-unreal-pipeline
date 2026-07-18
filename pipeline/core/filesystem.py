"""Filesystem-backed validation context."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata


class FilesystemContext(ValidationContext):
    """Discover on-disk files and expose them as AssetMetadata."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def get_assets(self) -> list[AssetMetadata]:
        paths = sorted(
            path.resolve()
            for path in self.root.rglob("*")
            if path.is_file()
        )
        assets: list[AssetMetadata] = []
        for path in paths:
            meta = self.get_asset_metadata(str(path))
            if meta is not None:
                assets.append(meta)
        return assets

    def get_asset_metadata(self, path: str) -> AssetMetadata | None:
        file_path = Path(path)
        if not file_path.is_file():
            return None
        resolved = file_path.resolve()
        return AssetMetadata(
            path=str(resolved),
            name=resolved.name,
            extension=resolved.suffix.lower(),
            size_bytes=resolved.stat().st_size,
            asset_class="",
        )

    def load_uobject(self, path: str) -> Any:
        del path
        return None
