"""Geometry-domain rule base (reserved for future mesh checks)."""

from pipeline.rules.validation_rule import ValidationRule
from pipeline.rules.models import RuleCategory


class GeometryRule(ValidationRule):
    category = RuleCategory.GEOMETRY
