"""Read-only Unreal material queries for materials-domain rules."""

from __future__ import annotations

from typing import Any

from pipeline.unreal.env import UNREAL_AVAILABLE, unreal


def as_material_interface(loaded: Any) -> Any | None:
    if not UNREAL_AVAILABLE or unreal is None or loaded is None:
        return None
    if isinstance(loaded, unreal.MaterialInterface):
        return loaded
    return None


def get_base_material(mi: Any) -> Any | None:
    assert unreal is not None
    try:
        base = mi.get_base_material()
    except Exception as exc:
        unreal.log_warning(f"materials: get_base_material failed: {exc}")
        return None
    if base is None or not isinstance(base, unreal.Material):
        return None
    return base


def material_editing_library() -> Any | None:
    if not UNREAL_AVAILABLE or unreal is None:
        return None
    mel = getattr(unreal, "MaterialEditingLibrary", None)
    if mel is None:
        unreal.log_warning("materials: MaterialEditingLibrary unavailable")
    return mel


def list_scalar_names(mi: Any) -> list[str] | None:
    return _list_param_names(mi, "get_scalar_parameter_names")


def list_vector_names(mi: Any) -> list[str] | None:
    return _list_param_names(mi, "get_vector_parameter_names")


def list_texture_names(mi: Any) -> list[str] | None:
    return _list_param_names(mi, "get_texture_parameter_names")


def has_param_name(mi: Any, kind: str, name: str) -> bool | None:
    """Return whether *name* exists; None if parameter lists cannot be read."""
    listers = {
        "scalar": list_scalar_names,
        "vector": list_vector_names,
        "texture": list_texture_names,
    }
    lister = listers.get(kind)
    if lister is None:
        return None
    names = lister(mi)
    if names is None:
        return None
    target = _normalize_param_name(name)
    return any(_normalize_param_name(n) == target for n in names)


def get_scalar(mi: Any, name: str) -> float | None:
    mel = material_editing_library()
    if mel is None or not name:
        return None
    assert unreal is not None
    try:
        if isinstance(mi, unreal.MaterialInstance):
            return float(mel.get_material_instance_scalar_parameter_value(mi, name))
        base = get_base_material(mi) or mi
        if not isinstance(base, unreal.Material):
            return None
        return float(mel.get_material_default_scalar_parameter_value(base, name))
    except Exception as exc:
        unreal.log_warning(f"materials: get_scalar({name!r}) failed: {exc}")
        return None


def get_vector(mi: Any, name: str) -> Any | None:
    mel = material_editing_library()
    if mel is None or not name:
        return None
    assert unreal is not None
    try:
        if isinstance(mi, unreal.MaterialInstance):
            return mel.get_material_instance_vector_parameter_value(mi, name)
        base = get_base_material(mi) or mi
        if not isinstance(base, unreal.Material):
            return None
        return mel.get_material_default_vector_parameter_value(base, name)
    except Exception as exc:
        unreal.log_warning(f"materials: get_vector({name!r}) failed: {exc}")
        return None


def get_texture(mi: Any, name: str) -> Any | None:
    mel = material_editing_library()
    if mel is None or not name:
        return None
    assert unreal is not None
    try:
        if isinstance(mi, unreal.MaterialInstance):
            return mel.get_material_instance_texture_parameter_value(mi, name)
        base = get_base_material(mi) or mi
        if not isinstance(base, unreal.Material):
            return None
        return mel.get_material_default_texture_parameter_value(base, name)
    except Exception as exc:
        unreal.log_warning(f"materials: get_texture({name!r}) failed: {exc}")
        return None


def texture_is_srgb(texture: Any) -> bool | None:
    if not UNREAL_AVAILABLE or unreal is None or texture is None:
        return None
    if not isinstance(texture, unreal.Texture):
        return None
    try:
        return bool(texture.get_editor_property("srgb"))
    except Exception:
        try:
            return bool(getattr(texture, "srgb"))
        except Exception as exc:
            unreal.log_warning(f"materials: failed to read texture srgb: {exc}")
            return None


def enum_token(value: Any) -> str:
    """Normalize Unreal enum / property values for allowlist comparison.

    Handles forms like ``MD_SURFACE``, ``MaterialDomain.MD_SURFACE``, and
    ``<MaterialDomain.MD_SURFACE: 0>``.
    """
    raw = ""
    for attr in ("name", "value"):
        attr_value = getattr(value, attr, None)
        if isinstance(attr_value, str) and attr_value.strip():
            raw = attr_value.strip()
            break
    if not raw:
        raw = str(value).strip()

    # ``<MaterialDomain.MD_SURFACE: 0>`` → ``MD_SURFACE``
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    if ":" in raw:
        raw = raw.split(":", 1)[0].strip()
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1]

    upper = raw.upper()
    for prefix in ("MSM_", "BLEND_", "MD_", "MATERIAL_DOMAIN_", "EMATERIALDOMAIN_"):
        if upper.startswith(prefix):
            raw = raw[len(prefix) :]
            break
    return raw.replace("_", "").replace(" ", "").lower()


def _list_param_names(mi: Any, method_name: str) -> list[str] | None:
    mel = material_editing_library()
    if mel is None:
        return None
    assert unreal is not None
    try:
        method = getattr(mel, method_name)
        raw = method(mi)
    except Exception as exc:
        unreal.log_warning(f"materials: {method_name} failed: {exc}")
        return None
    return [_name_to_str(item) for item in _iter_names(raw)]


def _iter_names(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, (list, tuple)):
        return list(raw)
    try:
        return list(raw)
    except TypeError:
        return [raw]


def _name_to_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _normalize_param_name(name: str) -> str:
    return str(name).strip().lower()
