from __future__ import annotations

from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.rules.models import RuleCategory, RuleResult, Severity
from pipeline.rules.validation_rule import ValidationRule, normalize_extensions


class FileFormatRule(ValidationRule):
    name = "file_format"
    category = RuleCategory.FILESYSTEM

    def __init__(
        self,
        enabled: bool,
        allowed_extensions: list[str],
        apply_to_extensions: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.allowed_extensions = normalize_extensions(allowed_extensions)
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> FileFormatRule:
        return cls(
            enabled=True,
            allowed_extensions=settings.get(
                "allowed_extensions",
                [".usd", ".usda", ".usdc", ".usdz"],
            ),
            apply_to_extensions=settings.get("apply_to_extensions"),
        )

    def validate(
        self, asset: AssetMetadata, ctx: ValidationContext
    ) -> list[RuleResult]:
        del ctx
        suffix = asset.extension.lower()
        if suffix in self.allowed_extensions:
            return [
                RuleResult(
                    severity=Severity.INFO,
                    rule=self.name,
                    category=self.category,
                    message="Allowed file format",
                )
            ]

        return [
            RuleResult(
                severity=Severity.ERROR,
                rule=self.name,
                category=self.category,
                message=f"Unsupported file format: {suffix}",
            )
        ]
