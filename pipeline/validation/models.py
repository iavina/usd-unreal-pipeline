"""Validation result objects produced by rules and consumed by renderers."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class RuleResult:
    severity: Severity
    rule: str
    message: str


@dataclass
class FileValidationResult:
    file: Path
    rule_results: list[RuleResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(result.severity != Severity.ERROR for result in self.rule_results)

    @property
    def failed_rule_results(self) -> list[RuleResult]:
        return [
            result
            for result in self.rule_results
            if result.severity == Severity.ERROR
        ]
