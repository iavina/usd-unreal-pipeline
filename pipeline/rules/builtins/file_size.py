from pathlib import Path

from pipeline.rules.validation_rule import ValidationRule
from pipeline.validation.models import RuleResult, Severity


class FileSizeRule(ValidationRule):
    name = "file_size"

    def __init__(self, enabled: bool, max_bytes: int) -> None:
        self.enabled = enabled
        self.max_bytes = max_bytes

    def validate(self, file: Path) -> list[RuleResult]:
        size = file.stat().st_size
        if size <= self.max_bytes:
            return [
                RuleResult(
                    severity=Severity.INFO,
                    rule=self.name,
                    message="File size within limit",
                )
            ]

        return [
            RuleResult(
                severity=Severity.ERROR,
                rule=self.name,
                message=f"File exceeds max size of {self.max_bytes} bytes",
            )
        ]
