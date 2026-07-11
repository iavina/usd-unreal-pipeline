"""Register and construct validation rules from configuration."""

from __future__ import annotations

from pipeline.config.models import PipelineConfig
from pipeline.rules.validation_rule import ValidationRule

_REGISTERED_RULES: list[type[ValidationRule]] = []


def register_rule(cls: type[ValidationRule]) -> type[ValidationRule]:
    """Decorator that adds a rule class to the registry when its module is imported."""
    if cls not in _REGISTERED_RULES:
        _REGISTERED_RULES.append(cls)
    return cls


def load_rule_packages() -> None:
    """Import category packages so @register_rule decorators run."""
    import pipeline.rules.filesystem  # noqa: F401
    import pipeline.rules.geometry  # noqa: F401
    import pipeline.rules.textures  # noqa: F401
    import pipeline.rules.unreal  # noqa: F401


def build_rules(config: PipelineConfig) -> list[ValidationRule]:
    """Construct enabled rules whose categories are enabled."""
    load_rule_packages()
    rules: list[ValidationRule] = []

    for rule_cls in _REGISTERED_RULES:
        settings = config.rule_settings(rule_cls.name)
        if not settings.get("enabled", False):
            continue
        if not config.category_enabled(rule_cls.category.value):
            continue
        rules.append(rule_cls.from_settings(settings))

    return rules
