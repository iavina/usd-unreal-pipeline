"""Contract implemented by all configurable validation rules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from pipeline.rules.models import RuleCategory, RuleResult, Severity

if TYPE_CHECKING:
    from pipeline.core.context import ValidationContext
    from pipeline.core.metadata import AssetMetadata


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

    def applies_to(self, asset: AssetMetadata, ctx: ValidationContext) -> bool:
        """Return whether this rule should run for the given asset."""
        del ctx
        if not self.apply_to_extensions:
            return True
        return asset.extension.lower() in self.apply_to_extensions

    def make_skipped(self, reason: str) -> RuleResult:
        """Non-failing skip when a host dependency is unavailable."""
        return RuleResult(
            severity=Severity.INFO,
            rule=self.name,
            category=self.category,
            message=f"[SKIPPED] {reason}",
            skipped=True,
        )

    @abstractmethod
    def validate(
        self, asset: AssetMetadata, ctx: ValidationContext
    ) -> list[RuleResult]:
        """Validate a single asset and return rule-level results."""
