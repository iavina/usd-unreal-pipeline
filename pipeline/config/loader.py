"""Load pipeline configuration from built-in defaults and JSON overrides."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import typer

from pipeline.config.defaults import DEFAULT_CONFIG
from pipeline.config.models import PipelineConfig


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
        return PipelineConfig(
            categories=config_data["categories"],
            rules=config_data["rules"],
        )

    if not config_path.exists():
        raise typer.BadParameter(f"Config file does not exist: {config_path}")

    try:
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise typer.BadParameter(f"Invalid config file: {config_path}") from None

    if not isinstance(loaded, dict):
        raise typer.BadParameter(f"Invalid config file: {config_path}")

    override: dict[str, Any] = {}
    if "categories" in loaded and isinstance(loaded["categories"], dict):
        override["categories"] = loaded["categories"]
    if "rules" in loaded and isinstance(loaded["rules"], dict):
        override["rules"] = loaded["rules"]

    if override:
        config_data = _deep_merge(config_data, override)

    return PipelineConfig(
        categories=config_data["categories"],
        rules=config_data["rules"],
    )
