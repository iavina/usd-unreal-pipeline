from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class LogEntry:
    severity: Severity
    rule: str
    file: Path
    message: str


@dataclass(frozen=True)
class FailedRule:
    rule: str
    message: str


@dataclass
class FileValidationResult:
    file: Path
    passed: bool
    failed_rules: list[FailedRule] = field(default_factory=list)
