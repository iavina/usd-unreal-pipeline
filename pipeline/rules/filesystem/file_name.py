from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.rules.filesystem.base import FilesystemRule
from pipeline.rules.registry import register_rule
from pipeline.rules.validation_rule import normalize_extensions
from pipeline.rules.models import RuleResult, Severity


@register_rule
class FileNameRule(FilesystemRule):
    name = "file_name"

    def __init__(
        self,
        enabled: bool,
        forbid_spaces: bool,
        apply_to_extensions: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.forbid_spaces = forbid_spaces
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> FileNameRule:
        return cls(
            enabled=True,
            forbid_spaces=bool(settings.get("forbid_spaces", True)),
            apply_to_extensions=settings.get("apply_to_extensions"),
        )

    def validate(self, file: Path) -> list[RuleResult]:
        if self.forbid_spaces and " " in file.name:
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
