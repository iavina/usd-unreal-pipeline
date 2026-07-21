from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "categories": {
        "filesystem": True,
        "geometry": False,
        "textures": False,
        "unreal": False,
        "materials": False,
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
            "rule_ignore": [],
        },
        "file_size": {
            "enabled": True,
            "warn_bytes": 83886080,
            "max_bytes": 104857600,
            "apply_to_extensions": [],
            "rule_ignore": [],
        },
        "file_name": {
            "enabled": True,
            "forbid_spaces": True,
            "apply_to_extensions": [],
            "rule_ignore": [],
        },
        "unreal_path": {
            "enabled": True,
            "require_prefix": "/Game",
            "forbid_spaces": True,
            "apply_to_extensions": [],
            "rule_ignore": [],
        },
        "mesh_closed": {
            "enabled": True,
            "require_closed": True,
            "apply_to_extensions": [],
            "rule_ignore": [],
        },
        "texture_max_resolution": {
            "enabled": True,
            "max_resolution": 2048,
            "apply_to_extensions": [],
            "rule_ignore": [],
        },
        "material_is_pbr": {
            "enabled": True,
            "shading_models": ["DefaultLit"],
            "blend_modes": ["Opaque"],
            "base_color_vector_name": "BaseColor",
            "base_color_texture_name": "BaseColor",
            "metallic_name": "Metallic",
            "roughness_name": "Roughness",
            "metallic_min": 0.0,
            "metallic_max": 1.0,
            "roughness_min": 0.0,
            "roughness_max": 1.0,
            "apply_to_extensions": [],
            "rule_ignore": [],
        },
        "material_normals_ok": {
            "enabled": True,
            "normal_texture_name": "Normal",
            "require_tangent_space": True,
            "require_normal_map": False,
            "require_linear_normal_map": True,
            "apply_to_extensions": [],
            "rule_ignore": [],
        },
    },
}
