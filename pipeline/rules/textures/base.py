"""Texture-domain rule base (reserved for future texture checks)."""

from pipeline.rules.validation_rule import ValidationRule
from pipeline.rules.models import RuleCategory


class TexturesRule(ValidationRule):
    category = RuleCategory.TEXTURES
