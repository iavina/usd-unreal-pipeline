"""Content Browser context menus that call the Unreal validation host."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import unreal
from unreal import Name, Text

from bootstrap import ensure_repo_on_sys_path, purge_pipeline_modules
from paths import normalize_asset_path, normalize_folder_path

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "unreal_validate_config.json"
_REGISTERED = False


def _load_run_validation():
    """Purge cached pipeline modules, then import a fresh host entry."""
    ensure_repo_on_sys_path()
    purge_pipeline_modules()
    from pipeline.unreal import run_validation

    return run_validation


def _selected_folder_paths() -> list[str]:
    raw = list(unreal.EditorUtilityLibrary.get_selected_path_view_folder_paths())
    return [normalize_folder_path(str(path)) for path in raw if str(path).strip()]


def _selected_asset_paths() -> list[str]:
    paths: list[str] = []
    asset_data_list = list(unreal.EditorUtilityLibrary.get_selected_asset_data())
    for asset_data in asset_data_list:
        package_name = str(getattr(asset_data, "package_name", "") or "")
        asset_name = str(getattr(asset_data, "asset_name", "") or "")
        object_path = str(getattr(asset_data, "object_path", "") or "")
        if object_path:
            paths.append(normalize_asset_path(object_path))
        elif package_name and asset_name:
            paths.append(normalize_asset_path(f"{package_name}.{asset_name}"))
        elif package_name:
            paths.append(normalize_asset_path(package_name))
    # Preserve order, drop duplicates
    seen: set[str] = set()
    unique: list[str] = []
    for path in paths:
        if path and path not in seen:
            seen.add(path)
            unique.append(path)
    return unique


@unreal.uclass()
class ValidateFolderScript(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context: Any) -> None:
        folders = _selected_folder_paths()
        if not folders:
            unreal.log_warning("[Validator] No folder selected.")
            return
        try:
            run_validation = _load_run_validation()
            for folder in folders:
                unreal.log(f"[Validator] Validating folder: {folder}")
                run_validation(config_path=_CONFIG_PATH, content_root=folder)
        except Exception as exc:
            unreal.log_error(f"[Validator] Folder validation failed: {exc}")


@unreal.uclass()
class ValidateAssetScript(unreal.ToolMenuEntryScript):
    @unreal.ufunction(override=True)
    def execute(self, context: Any) -> None:
        assets = _selected_asset_paths()
        if not assets:
            unreal.log_warning("[Validator] No assets selected.")
            return
        try:
            run_validation = _load_run_validation()
            unreal.log(f"[Validator] Validating {len(assets)} asset(s)")
            run_validation(config_path=_CONFIG_PATH, asset_paths=assets)
        except Exception as exc:
            unreal.log_error(f"[Validator] Asset validation failed: {exc}")


def register_all() -> None:
    """Attach folder and asset Validate entries (idempotent)."""
    global _REGISTERED
    if _REGISTERED:
        return

    folder_menu = "ContentBrowser.FolderContextMenu"
    folder_entry = ValidateFolderScript()
    folder_entry.init_entry(
        owner_name=Name(folder_menu),
        menu=Name(folder_menu),
        section=Name("PathViewFolderOptions"),
        name=Name("ValidateFolder"),
        label=Text("Validate Folder"),
    )
    folder_entry.register_menu_entry()

    asset_menu = "ContentBrowser.AssetContextMenu"
    asset_entry = ValidateAssetScript()
    asset_entry.init_entry(
        owner_name=Name(asset_menu),
        menu=Name(asset_menu),
        section=Name("CommonAssetActions"),
        name=Name("ValidateAssets"),
        label=Text("Validate Assets"),
    )
    asset_entry.register_menu_entry()

    _REGISTERED = True
    unreal.log("[Validator] Content Browser validation menus registered.")
