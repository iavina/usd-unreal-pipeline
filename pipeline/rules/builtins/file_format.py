from pathlib import Path

from pipeline.logging import LogEntry, Severity
from pipeline.rules.validation_rule import ValidationRule


class FileFormatRule(ValidationRule):
    name = "file_format"

    def __init__(self, enabled: bool, allowed_extensions: list[str]) -> None:
        self.enabled = enabled
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]

    def validate(self, file: Path) -> list[LogEntry]:
        suffix = file.suffix.lower()
        if suffix in self.allowed_extensions:
            return [
                LogEntry(
                    severity=Severity.INFO,
                    rule=self.name,
                    file=file,
                    message="Allowed file format",
                )
            ]

        return [
            LogEntry(
                severity=Severity.ERROR,
                rule=self.name,
                file=file,
                message=f"Unsupported file format: {suffix}",
            )
        ]
