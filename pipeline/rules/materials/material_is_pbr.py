from __future__ import annotations

from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.rules.materials import _material_helpers as helpers
from pipeline.rules.models import RuleCategory, RuleResult, Severity
from pipeline.rules.path_ignore import common_filter_kwargs, normalize_rule_ignore
from pipeline.rules.validation_rule import ValidationRule, normalize_extensions
from pipeline.unreal.env import UNREAL_AVAILABLE, unreal


class MaterialIsPbrRule(ValidationRule):
    """Unreal-only: named-parameter PBR convention on MaterialInterface assets."""

    name = "material_is_pbr"
    category = RuleCategory.MATERIALS

    def __init__(
        self,
        enabled: bool,
        shading_models: list[str],
        blend_modes: list[str],
        base_color_vector_name: str,
        base_color_texture_name: str,
        metallic_name: str,
        roughness_name: str,
        metallic_min: float,
        metallic_max: float,
        roughness_min: float,
        roughness_max: float,
        apply_to_extensions: list[str] | None = None,
        rule_ignore: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.shading_models = shading_models
        self.blend_modes = blend_modes
        self.base_color_vector_name = base_color_vector_name
        self.base_color_texture_name = base_color_texture_name
        self.metallic_name = metallic_name
        self.roughness_name = roughness_name
        self.metallic_min = metallic_min
        self.metallic_max = metallic_max
        self.roughness_min = roughness_min
        self.roughness_max = roughness_max
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)
        self.rule_ignore = normalize_rule_ignore(rule_ignore)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> MaterialIsPbrRule:
        return cls(
            enabled=True,
            shading_models=_string_list(
                settings.get("shading_models"), ["DefaultLit"]
            ),
            blend_modes=_string_list(settings.get("blend_modes"), ["Opaque"]),
            base_color_vector_name=str(
                settings.get("base_color_vector_name", "BaseColor")
            ),
            base_color_texture_name=str(
                settings.get("base_color_texture_name", "BaseColor")
            ),
            metallic_name=str(settings.get("metallic_name", "Metallic")),
            roughness_name=str(settings.get("roughness_name", "Roughness")),
            metallic_min=float(settings.get("metallic_min", 0.0)),
            metallic_max=float(settings.get("metallic_max", 1.0)),
            roughness_min=float(settings.get("roughness_min", 0.0)),
            roughness_max=float(settings.get("roughness_max", 1.0)),
            **common_filter_kwargs(settings),
        )

    def validate(
        self, asset: AssetMetadata, ctx: ValidationContext
    ) -> list[RuleResult]:
        if not UNREAL_AVAILABLE or unreal is None:
            return [self.make_skipped("Unreal Engine not available.")]

        mi = helpers.as_material_interface(ctx.load_uobject(asset.path))
        if mi is None:
            return []

        if helpers.material_editing_library() is None:
            return [self.make_skipped("MaterialEditingLibrary not available.")]

        base = helpers.get_base_material(mi)
        if base is None:
            return [
                self._error("could not resolve base Material"),
            ]

        # Only enforce named PBR params on PBR-shaped materials. Other domains /
        # shading models / blend modes are skipped with an explicit log.
        domain = _read_property(base, "material_domain")
        if domain is None or helpers.enum_token(domain) != helpers.enum_token(
            "Surface"
        ):
            return [
                self.make_skipped(
                    "Not detected as PBR "
                    f"(material_domain={domain!s}; expected Surface)"
                )
            ]

        shading = _read_property(base, "shading_model")
        if not _in_allowlist(shading, self.shading_models):
            return [
                self.make_skipped(
                    "Not detected as PBR "
                    f"(shading_model={shading!s}; "
                    f"allowed={self.shading_models})"
                )
            ]

        blend = _read_property(base, "blend_mode")
        if not _in_allowlist(blend, self.blend_modes):
            return [
                self.make_skipped(
                    "Not detected as PBR "
                    f"(blend_mode={blend!s}; allowed={self.blend_modes})"
                )
            ]

        results: list[RuleResult] = []
        has_vector = helpers.has_param_name(mi, "vector", self.base_color_vector_name)
        has_texture = helpers.has_param_name(
            mi, "texture", self.base_color_texture_name
        )
        if has_vector is None or has_texture is None:
            return [self.make_skipped("MaterialEditingLibrary not available.")]
        if not has_vector and not has_texture:
            results.append(
                self._error(
                    "missing BaseColor parameter "
                    f"(vector={self.base_color_vector_name!r} or "
                    f"texture={self.base_color_texture_name!r})"
                )
            )

        results.extend(
            self._check_scalar_range(
                mi,
                self.metallic_name,
                self.metallic_min,
                self.metallic_max,
            )
        )
        results.extend(
            self._check_scalar_range(
                mi,
                self.roughness_name,
                self.roughness_min,
                self.roughness_max,
            )
        )

        if results:
            return results
        return [
            RuleResult(
                severity=Severity.INFO,
                rule=self.name,
                category=self.category,
                message="Material satisfies PBR convention",
            )
        ]

    def _check_scalar_range(
        self,
        mi: Any,
        name: str,
        minimum: float,
        maximum: float,
    ) -> list[RuleResult]:
        present = helpers.has_param_name(mi, "scalar", name)
        if present is None:
            return [self.make_skipped("MaterialEditingLibrary not available.")]
        if not present:
            return [self._error(f"missing scalar parameter {name!r}")]

        value = helpers.get_scalar(mi, name)
        if value is None:
            return [self._error(f"could not read scalar parameter {name!r}")]
        if value < minimum or value > maximum:
            return [
                self._error(
                    f"{name}={value} outside [{minimum}, {maximum}]"
                )
            ]
        return []

    def _error(self, message: str) -> RuleResult:
        return RuleResult(
            severity=Severity.ERROR,
            rule=self.name,
            category=self.category,
            message=message,
        )


def _string_list(value: Any, default: list[str]) -> list[str]:
    if not isinstance(value, list) or not value:
        return list(default)
    return [str(item) for item in value]


def _read_property(obj: Any, name: str) -> Any | None:
    try:
        return obj.get_editor_property(name)
    except Exception:
        return getattr(obj, name, None)


def _in_allowlist(value: Any, allowlist: list[str]) -> bool:
    if value is None:
        return False
    token = helpers.enum_token(value)
    return any(helpers.enum_token(allowed) == token for allowed in allowlist)
