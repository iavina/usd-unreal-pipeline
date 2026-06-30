from pathlib import Path

from pipeline.rules.validation_rule import ValidationRule
from pipeline.validation.models import RuleResult, Severity


class FileFormatRule(ValidationRule):
    name = "file_format"

    def __init__(self, enabled: bool, allowed_extensions: list[str]) -> None:
        self.enabled = enabled
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]

    def validate(self, file: Path) -> list[RuleResult]:
        suffix = file.suffix.lower()
        if suffix in self.allowed_extensions:
            return [
                RuleResult(
                    severity=Severity.INFO,
                    rule=self.name,
                    message="Allowed file format",
                )
            ]

        return [
            RuleResult(
                severity=Severity.ERROR,
                rule=self.name,
                message=f"Unsupported file format: {suffix}",
            )
        ]
