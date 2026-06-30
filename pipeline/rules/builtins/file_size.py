from pathlib import Path

from pipeline.logging import LogEntry, Severity
from pipeline.rules.validation_rule import ValidationRule


class FileSizeRule(ValidationRule):
    name = "file_size"

    def __init__(self, enabled: bool, max_bytes: int) -> None:
        self.enabled = enabled
        self.max_bytes = max_bytes

    def validate(self, file: Path) -> list[LogEntry]:
        size = file.stat().st_size
        if size <= self.max_bytes:
            return [
                LogEntry(
                    severity=Severity.INFO,
                    rule=self.name,
                    file=file,
                    message="File size within limit",
                )
            ]

        return [
            LogEntry(
                severity=Severity.ERROR,
                rule=self.name,
                file=file,
                message=f"File exceeds max size of {self.max_bytes} bytes",
            )
        ]
