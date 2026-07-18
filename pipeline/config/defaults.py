from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "categories": {
        "filesystem": True,
        "geometry": False,
        "textures": False,
        "unreal": False,
    },
    "host": {
        # Unreal discovery root (Content Browser path). Ignored by CLI.
        "content_root": "/Game/ExampleContent",
    },
    "rules": {
        "file_format": {
            "enabled": True,
            "allowed_extensions": [".usd", ".usda", ".usdc", ".usdz"],
            "apply_to_extensions": [],
        },
        "file_size": {
            "enabled": True,
            "warn_bytes": 83886080,
            "max_bytes": 104857600,
            "apply_to_extensions": [],
        },
        "file_name": {
            "enabled": True,
            "forbid_spaces": True,
            "apply_to_extensions": [],
        },
        "unreal_path": {
            "enabled": True,
            "require_prefix": "/Game",
            "forbid_spaces": True,
            "apply_to_extensions": [],
        },
        "mesh_closed": {
            "enabled": True,
            "require_closed": True,
            "apply_to_extensions": [],
        },
        "texture_max_resolution": {
            "enabled": True,
            "max_resolution": 2048,
            "apply_to_extensions": [],
        },
    },
}
