from __future__ import annotations

from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.rules.models import RuleCategory, RuleResult, Severity
from pipeline.rules.path_ignore import common_filter_kwargs, normalize_rule_ignore
from pipeline.rules.validation_rule import ValidationRule, normalize_extensions


class FileNameRule(ValidationRule):
    name = "file_name"
    category = RuleCategory.FILESYSTEM

    def __init__(
        self,
        enabled: bool,
        forbid_spaces: bool,
        apply_to_extensions: list[str] | None = None,
        rule_ignore: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.forbid_spaces = forbid_spaces
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)
        self.rule_ignore = normalize_rule_ignore(rule_ignore)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> FileNameRule:
        return cls(
            enabled=True,
            forbid_spaces=bool(settings.get("forbid_spaces", True)),
            **common_filter_kwargs(settings),
        )

    def validate(
        self, asset: AssetMetadata, ctx: ValidationContext
    ) -> list[RuleResult]:
        del ctx
        if self.forbid_spaces and " " in asset.name:
            return [
                RuleResult(
                    severity=Severity.ERROR,
                    rule=self.name,
                    category=self.category,
                    message="Filename contains spaces",
                )
            ]

        return [
            RuleResult(
                severity=Severity.INFO,
                rule=self.name,
                category=self.category,
                message="Filename passed naming check",
            )
        ]
