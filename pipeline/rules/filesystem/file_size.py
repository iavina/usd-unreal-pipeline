from __future__ import annotations

from pathlib import Path
from typing import Any

from pipeline.rules.filesystem.base import FilesystemRule
from pipeline.rules.registry import register_rule
from pipeline.rules.validation_rule import normalize_extensions
from pipeline.rules.models import RuleResult, Severity


@register_rule
class FileSizeRule(FilesystemRule):
    name = "file_size"

    def __init__(
        self,
        enabled: bool,
        warn_bytes: int,
        max_bytes: int,
        apply_to_extensions: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.warn_bytes = warn_bytes
        self.max_bytes = max_bytes
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> FileSizeRule:
        return cls(
            enabled=True,
            warn_bytes=int(settings.get("warn_bytes", 83886080)),
            max_bytes=int(settings.get("max_bytes", 104857600)),
            apply_to_extensions=settings.get("apply_to_extensions"),
        )

    def validate(self, file: Path) -> list[RuleResult]:
        size = file.stat().st_size
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
