from dataclasses import dataclass
from typing import Any


@dataclass
class PipelineConfig:
    categories: dict[str, Any]
    rules: dict[str, Any]

    def category_enabled(self, category: str) -> bool:
        return bool(self.categories.get(category, False))

    def rule_settings(self, name: str) -> dict[str, Any]:
        rule = self.rules.get(name, {})
        return rule if isinstance(rule, dict) else {}
