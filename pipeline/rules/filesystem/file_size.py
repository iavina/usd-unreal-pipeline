from __future__ import annotations

from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.rules.models import RuleCategory, RuleResult, Severity
from pipeline.rules.path_ignore import common_filter_kwargs, normalize_rule_ignore
from pipeline.rules.validation_rule import ValidationRule, normalize_extensions


class FileSizeRule(ValidationRule):
    name = "file_size"
    category = RuleCategory.FILESYSTEM

    def __init__(
        self,
        enabled: bool,
        warn_bytes: int,
        max_bytes: int,
        apply_to_extensions: list[str] | None = None,
        rule_ignore: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.warn_bytes = warn_bytes
        self.max_bytes = max_bytes
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)
        self.rule_ignore = normalize_rule_ignore(rule_ignore)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> FileSizeRule:
        return cls(
            enabled=True,
            warn_bytes=int(settings.get("warn_bytes", 83886080)),
            max_bytes=int(settings.get("max_bytes", 104857600)),
            **common_filter_kwargs(settings),
        )

    def validate(
        self, asset: AssetMetadata, ctx: ValidationContext
    ) -> list[RuleResult]:
        del ctx
        size = asset.size_bytes

        if size > self.max_bytes:
            return [
                RuleResult(
                    severity=Severity.ERROR,
                    rule=self.name,
                    category=self.category,
                    message=f"File exceeds max size of {self.max_bytes} bytes",
                )
            ]

        if size > self.warn_bytes:
            return [
                RuleResult(
                    severity=Severity.WARNING,
                    rule=self.name,
                    category=self.category,
                    message=(
                        f"File size exceeds soft limit of {self.warn_bytes} bytes"
                    ),
                )
            ]

        return [
            RuleResult(
                severity=Severity.INFO,
                rule=self.name,
                category=self.category,
                message="File size within limit",
            )
        ]
