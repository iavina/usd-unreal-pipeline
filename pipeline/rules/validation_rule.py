"""Contract implemented by all configurable validation rules."""

from abc import ABC, abstractmethod
from pathlib import Path

from pipeline.logging import LogEntry


class ValidationRule(ABC):
    name: str
    enabled: bool

    @abstractmethod
    def validate(self, file: Path) -> list[LogEntry]:
        """Validate a single file and return rule-level log entries."""
