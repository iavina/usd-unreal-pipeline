from __future__ import annotations

from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.rules.models import RuleCategory, RuleResult, Severity
from pipeline.rules.path_ignore import common_filter_kwargs, normalize_rule_ignore
from pipeline.rules.validation_rule import ValidationRule, normalize_extensions
from pipeline.unreal.env import UNREAL_AVAILABLE, unreal


class TextureMaxResolutionRule(ValidationRule):
    """Unreal-only: Texture2D max resolution check."""

    name = "texture_max_resolution"
    category = RuleCategory.TEXTURES

    def __init__(
        self,
        enabled: bool,
        max_resolution: int,
        apply_to_extensions: list[str] | None = None,
        rule_ignore: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.max_resolution = max_resolution
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)
        self.rule_ignore = normalize_rule_ignore(rule_ignore)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> TextureMaxResolutionRule:
        return cls(
            enabled=True,
            max_resolution=int(settings.get("max_resolution", 2048)),
            **common_filter_kwargs(settings),
        )

    def validate(
        self, asset: AssetMetadata, ctx: ValidationContext
    ) -> list[RuleResult]:
        if not UNREAL_AVAILABLE or unreal is None:
            return [self.make_skipped("Unreal Engine not available.")]

        size = _texture_size(ctx.load_uobject(asset.path))
        if size is None:
            return []

        width, height = size
        dims = f"{width}x{height}"
        if max(width, height) > self.max_resolution:
            return [
                RuleResult(
                    severity=Severity.ERROR,
                    rule=self.name,
                    category=self.category,
                    message=(
                        f"Texture resolution {dims} exceeds max "
                        f"{self.max_resolution}"
                    ),
                )
            ]

        return [
            RuleResult(
                severity=Severity.INFO,
                rule=self.name,
                category=self.category,
                message=(
                    f"Texture resolution {dims} within max "
                    f"{self.max_resolution}"
                ),
            )
        ]


def _texture_size(loaded: Any) -> tuple[int, int] | None:
    assert unreal is not None
    if loaded is None or not isinstance(loaded, unreal.Texture2D):
        return None

    try:
        width = int(loaded.blueprint_get_size_x())
        height = int(loaded.blueprint_get_size_y())
    except Exception:
        try:
            imported = loaded.get_editor_property("imported_size")
            width = int(imported.x)
            height = int(imported.y)
        except Exception as exc:
            unreal.log_warning(f"texture_max_resolution: failed to read size: {exc}")
            return None

    if width <= 0 or height <= 0:
        return None
    return width, height
