from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "rules": {
        "file_format": {
            "enabled": True,
            "allowed_extensions": [".usd", ".usda", ".usdc", ".usdz"],
        },
        "file_size": {
            "enabled": True,
            "max_bytes": 104857600,
        },
    }
}
