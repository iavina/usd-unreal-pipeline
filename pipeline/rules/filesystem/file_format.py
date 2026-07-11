from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.rules.filesystem.base import FilesystemRule
from pipeline.rules.registry import register_rule
from pipeline.rules.validation_rule import normalize_extensions
from pipeline.rules.models import RuleResult, Severity


@register_rule
class FileFormatRule(FilesystemRule):
    name = "file_format"

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

    def validate(self, file: Path) -> list[RuleResult]:
        suffix = file.suffix.lower()
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
