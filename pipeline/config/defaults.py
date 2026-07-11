from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "categories": {
        "filesystem": True,
        "geometry": False,
        "textures": False,
        "unreal": False,
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
    },
}
