"""Load pipeline configuration from built-in defaults and JSON overrides."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pipeline.config.defaults import DEFAULT_CONFIG


class ConfigError(ValueError):
    """Raised when a config file is missing or invalid."""


@dataclass
class PipelineConfig:
    categories: dict[str, Any]
    rules: dict[str, Any]
    host: dict[str, Any]

    def category_enabled(self, category: str) -> bool:
        return bool(self.categories.get(category, False))

    def rule_settings(self, name: str) -> dict[str, Any]:
        rule = self.rules.get(name, {})
        return rule if isinstance(rule, dict) else {}

    @property
    def content_root(self) -> str:
        raw = self.host.get("content_root", "/Game/ExampleContent")
        return str(raw).rstrip("/") or "/Game/ExampleContent"


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: Path | None) -> PipelineConfig:
    config_data = copy.deepcopy(DEFAULT_CONFIG)

    if config_path is None:
        return _to_pipeline_config(config_data)

    if not config_path.exists():
        raise ConfigError(f"Config file does not exist: {config_path}")

    try:
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid config file: {config_path}") from exc

    if not isinstance(loaded, dict):
        raise ConfigError(f"Invalid config file: {config_path}")

    override: dict[str, Any] = {}
    if "categories" in loaded and isinstance(loaded["categories"], dict):
        override["categories"] = loaded["categories"]
    if "rules" in loaded and isinstance(loaded["rules"], dict):
        override["rules"] = loaded["rules"]
    if "host" in loaded and isinstance(loaded["host"], dict):
        override["host"] = loaded["host"]

    if override:
        config_data = _deep_merge(config_data, override)

    return _to_pipeline_config(config_data)


def _to_pipeline_config(config_data: dict[str, Any]) -> PipelineConfig:
    return PipelineConfig(
        categories=config_data["categories"],
        rules=config_data["rules"],
        host=config_data.get("host", {}),
    )
