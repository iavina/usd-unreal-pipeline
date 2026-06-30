"""Contract implemented by all configurable validation rules."""

from abc import ABC, abstractmethod
from pathlib import Path

from pipeline.validation.models import RuleResult


class ValidationRule(ABC):
    name: str
    enabled: bool

    @abstractmethod
    def validate(self, file: Path) -> list[RuleResult]:
        """Validate a single file and return rule-level results."""
