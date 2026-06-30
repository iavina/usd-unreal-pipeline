from dataclasses import dataclass
from typing import Any


@dataclass
class PipelineConfig:
    rules: dict[str, Any]

    def rule_settings(self, name: str) -> dict[str, Any]:
        rule = self.rules.get(name, {})
        return rule if isinstance(rule, dict) else {}
