from __future__ import annotations

from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.rules.models import RuleCategory, RuleResult, Severity
from pipeline.rules.path_ignore import common_filter_kwargs, normalize_rule_ignore
from pipeline.rules.validation_rule import ValidationRule, normalize_extensions


class FileFormatRule(ValidationRule):
    name = "file_format"
    category = RuleCategory.FILESYSTEM

    def __init__(
        self,
        enabled: bool,
        allowed_extensions: list[str],
        apply_to_extensions: list[str] | None = None,
        rule_ignore: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.allowed_extensions = normalize_extensions(allowed_extensions)
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)
        self.rule_ignore = normalize_rule_ignore(rule_ignore)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> FileFormatRule:
        return cls(
            enabled=True,
            allowed_extensions=settings.get(
                "allowed_extensions",
                [".usd", ".usda", ".usdc", ".usdz"],
            ),
            **common_filter_kwargs(settings),
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
