"""Unreal-backed validation context adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.unreal.constants import CONTENT_ROOT
from pipeline.unreal.env import UNREAL_AVAILABLE, unreal


def _package_size_bytes(unreal_mod: Any, object_path: str) -> int:
    package_name = object_path
    if "." in package_name:
        package_name = package_name.rsplit(".", 1)[0]

    if not package_name.startswith("/Game/"):
        return 0

    relative = package_name[len("/Game/") :]
    content_dir = Path(str(unreal_mod.Paths.project_content_dir()))
    package_file = content_dir / f"{relative}.uasset"
    if not package_file.is_file():
        return 0
    return package_file.stat().st_size


class UnrealContext(ValidationContext):
    """Discover Unreal assets and load UObjects for engine-side rules."""

    def __init__(self, asset_path: str = CONTENT_ROOT) -> None:
        if not UNREAL_AVAILABLE or unreal is None:
            raise ImportError(
                "UnrealContext requires Unreal Editor. "
                "Use FilesystemContext for standalone Python mode."
            )
        self._unreal = unreal
        self.asset_path = asset_path.rstrip("/") or CONTENT_ROOT

    def get_assets(self) -> list[AssetMetadata]:
        registry = self._unreal.AssetRegistryHelpers.get_asset_registry()
        asset_filter = self._unreal.ARFilter(
            package_paths=[self.asset_path],
            recursive_paths=True,
        )
        assets_data = list(registry.get_assets(asset_filter))
        assets: list[AssetMetadata] = []
        for asset_data in assets_data:
            package_name = str(asset_data.package_name)
            asset_name = str(asset_data.asset_name)
            object_path = f"{package_name}.{asset_name}"
            meta = self.get_asset_metadata(object_path)
            if meta is not None:
                assets.append(meta)
        return sorted(assets, key=lambda asset: asset.path)

    def get_asset_metadata(self, path: str) -> AssetMetadata | None:
        if not self._unreal.EditorAssetLibrary.does_asset_exist(path):
            return None

        asset_data = self._unreal.EditorAssetLibrary.find_asset_data(path)
        asset_class = ""
        name = path.rsplit("/", 1)[-1]
        if "." in name:
            name = name.rsplit(".", 1)[-1]

        if asset_data is not None:
            asset_class = str(
                getattr(asset_data, "asset_class_path", None)
                or getattr(asset_data, "asset_class", "")
                or ""
            )
            asset_name = getattr(asset_data, "asset_name", None)
            if asset_name is not None:
                name = str(asset_name)

        return AssetMetadata(
            path=path,
            name=name,
            extension="",
            size_bytes=_package_size_bytes(self._unreal, path),
            asset_class=asset_class,
        )

    def load_uobject(self, path: str) -> Any:
        return self._unreal.EditorAssetLibrary.load_asset(path)
