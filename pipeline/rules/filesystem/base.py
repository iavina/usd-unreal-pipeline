"""Filesystem-domain rule base."""

from pipeline.rules.validation_rule import ValidationRule
from pipeline.rules.models import RuleCategory


class FilesystemRule(ValidationRule):
    category = RuleCategory.FILESYSTEM
