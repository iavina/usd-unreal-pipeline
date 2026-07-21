from __future__ import annotations

from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.rules.models import RuleCategory, RuleResult, Severity
from pipeline.rules.path_ignore import common_filter_kwargs, normalize_rule_ignore
from pipeline.rules.validation_rule import ValidationRule, normalize_extensions


class UnrealPathRule(ValidationRule):
    name = "unreal_path"
    category = RuleCategory.UNREAL

    def __init__(
        self,
        enabled: bool,
        require_prefix: str,
        forbid_spaces: bool,
        apply_to_extensions: list[str] | None = None,
        rule_ignore: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.require_prefix = require_prefix
        self.forbid_spaces = forbid_spaces
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)
        self.rule_ignore = normalize_rule_ignore(rule_ignore)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> UnrealPathRule:
        return cls(
            enabled=True,
            require_prefix=str(settings.get("require_prefix", "/Game")),
            forbid_spaces=bool(settings.get("forbid_spaces", True)),
            **common_filter_kwargs(settings),
        )

    def validate(
        self, asset: AssetMetadata, ctx: ValidationContext
    ) -> list[RuleResult]:
        del ctx
        path = asset.path

        if self.forbid_spaces and " " in path:
            return [
                RuleResult(
                    severity=Severity.ERROR,
                    rule=self.name,
                    category=self.category,
                    message="Asset path contains spaces",
                )
            ]

        if not path.startswith(self.require_prefix):
            return [
                RuleResult(
                    severity=Severity.ERROR,
                    rule=self.name,
                    category=self.category,
                    message=(
                        f"Asset path must start with {self.require_prefix}"
                    ),
                )
            ]

        return [
            RuleResult(
                severity=Severity.INFO,
                rule=self.name,
                category=self.category,
                message="Asset path passed Unreal path check",
            )
        ]
