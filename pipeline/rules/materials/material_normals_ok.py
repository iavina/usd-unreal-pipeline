from __future__ import annotations

from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.rules.materials import _material_helpers as helpers
from pipeline.rules.models import RuleCategory, RuleResult, Severity
from pipeline.rules.path_ignore import common_filter_kwargs, normalize_rule_ignore
from pipeline.rules.validation_rule import ValidationRule, normalize_extensions
from pipeline.unreal.env import UNREAL_AVAILABLE, unreal


class MaterialNormalsOkRule(ValidationRule):
    """Unreal-only: tangent-space + Normal map binding / linear color space."""

    name = "material_normals_ok"
    category = RuleCategory.MATERIALS

    def __init__(
        self,
        enabled: bool,
        normal_texture_name: str,
        require_tangent_space: bool,
        require_normal_map: bool,
        require_linear_normal_map: bool,
        apply_to_extensions: list[str] | None = None,
        rule_ignore: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.normal_texture_name = normal_texture_name
        self.require_tangent_space = require_tangent_space
        self.require_normal_map = require_normal_map
        self.require_linear_normal_map = require_linear_normal_map
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)
        self.rule_ignore = normalize_rule_ignore(rule_ignore)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> MaterialNormalsOkRule:
        return cls(
            enabled=True,
            normal_texture_name=str(settings.get("normal_texture_name", "Normal")),
            require_tangent_space=bool(settings.get("require_tangent_space", True)),
            require_normal_map=bool(settings.get("require_normal_map", False)),
            require_linear_normal_map=bool(
                settings.get("require_linear_normal_map", True)
            ),
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

        results: list[RuleResult] = []
        base = helpers.get_base_material(mi)
        if base is None:
            return [self._error("could not resolve base Material")]

        if self.require_tangent_space:
            tangent_space = _read_bool_property(base, "tangent_space_normal")
            if tangent_space is False:
                results.append(
                    self._error("tangent_space_normal is false; expected true")
                )

        has_normal = helpers.has_param_name(mi, "texture", self.normal_texture_name)
        if has_normal is None:
            return [self.make_skipped("MaterialEditingLibrary not available.")]

        if not has_normal:
            if self.require_normal_map:
                results.append(
                    self._error(
                        f"missing Normal texture parameter "
                        f"{self.normal_texture_name!r}"
                    )
                )
            else:
                if results:
                    return results
                return [
                    RuleResult(
                        severity=Severity.INFO,
                        rule=self.name,
                        category=self.category,
                        message="No Normal map parameter (not required)",
                    )
                ]

        texture = helpers.get_texture(mi, self.normal_texture_name)
        if texture is None:
            results.append(self._error("Normal parameter unbound"))
        elif self.require_linear_normal_map:
            srgb = helpers.texture_is_srgb(texture)
            if srgb is True:
                results.append(
                    self._error("Normal map is sRGB; expected linear")
                )
            elif srgb is None:
                results.append(
                    RuleResult(
                        severity=Severity.WARNING,
                        rule=self.name,
                        category=self.category,
                        message="could not read Normal map sRGB flag",
                    )
                )

        if results:
            return results
        return [
            RuleResult(
                severity=Severity.INFO,
                rule=self.name,
                category=self.category,
                message="Material normals OK",
            )
        ]

    def _error(self, message: str) -> RuleResult:
        return RuleResult(
            severity=Severity.ERROR,
            rule=self.name,
            category=self.category,
            message=message,
        )


def _read_bool_property(obj: Any, name: str) -> bool | None:
    try:
        return bool(obj.get_editor_property(name))
    except Exception:
        value = getattr(obj, name, None)
        if value is None:
            return None
        return bool(value)
