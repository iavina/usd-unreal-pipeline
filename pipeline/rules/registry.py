"""Discover and construct validation rules from category packages."""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from pipeline.config.loader import PipelineConfig
from pipeline.rules.models import RuleCategory
from pipeline.rules.validation_rule import ValidationRule


def _discover_rule_classes(package_name: str) -> list[type[ValidationRule]]:
    """Import modules in a category package and collect concrete rule classes."""
    package = importlib.import_module(package_name)
    if not hasattr(package, "__path__"):
        return []

    discovered: list[type[ValidationRule]] = []
    for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        module_leaf = module_info.name.rsplit(".", 1)[-1]
        if module_leaf.startswith("_"):
            continue

        module = importlib.import_module(module_info.name)
        for obj in vars(module).values():
            if not isinstance(obj, type):
                continue
            if obj is ValidationRule or not issubclass(obj, ValidationRule):
                continue
            if inspect.isabstract(obj):
                continue
            if obj not in discovered:
                discovered.append(obj)

    return sorted(discovered, key=lambda rule_cls: rule_cls.name)


def build_rules(config: PipelineConfig) -> list[ValidationRule]:
    """Construct enabled rules from enabled category packages."""
    rules: list[ValidationRule] = []

    for category in RuleCategory:
        if not config.category_enabled(category.value):
            continue

        package_name = f"pipeline.rules.{category.value}"
        for rule_cls in _discover_rule_classes(package_name):
            settings = config.rule_settings(rule_cls.name)
            if not settings.get("enabled", False):
                continue
            if rule_cls.category is not category:
                continue
            rules.append(rule_cls.from_settings(settings))

    return rules
