"""Unreal-domain rule base (reserved for future engine-context checks)."""

from pipeline.rules.validation_rule import ValidationRule
from pipeline.rules.models import RuleCategory


class UnrealRule(ValidationRule):
    category = RuleCategory.UNREAL
