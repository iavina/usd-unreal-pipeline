"""Contract implemented by all configurable validation rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pipeline.rules.models import RuleCategory, RuleResult


def normalize_extensions(values: list[str] | None) -> list[str]:
    """Normalize extension filters to lowercase dotted suffixes."""
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        ext = value.lower()
        if ext and not ext.startswith("."):
            ext = f".{ext}"
        normalized.append(ext)
    return normalized


class ValidationRule(ABC):
    name: str
    category: RuleCategory
    enabled: bool
    apply_to_extensions: list[str]

    @classmethod
    @abstractmethod
    def from_settings(cls, settings: dict[str, Any]) -> ValidationRule:
        """Build a rule instance from its config settings dict."""

    def applies_to(self, file: Path) -> bool:
        """Return whether this rule should run for the given file."""
        if not self.apply_to_extensions:
            return True
        return file.suffix.lower() in self.apply_to_extensions

    @abstractmethod
    def validate(self, file: Path) -> list[RuleResult]:
        """Validate a single file and return rule-level results."""
