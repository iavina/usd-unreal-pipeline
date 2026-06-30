"""Build enabled validation rule instances from pipeline configuration."""

from pipeline.config import PipelineConfig
from pipeline.rules.builtins import FileFormatRule, FileSizeRule
from pipeline.rules.validation_rule import ValidationRule


def build_rules(config: PipelineConfig) -> list[ValidationRule]:
    rules: list[ValidationRule] = []

    format_settings = config.rule_settings("file_format")
    if format_settings.get("enabled", False):
        rules.append(
            FileFormatRule(
                enabled=True,
                allowed_extensions=format_settings.get(
                    "allowed_extensions",
                    [".usd", ".usda", ".usdc", ".usdz"],
                ),
            )
        )

    size_settings = config.rule_settings("file_size")
    if size_settings.get("enabled", False):
        rules.append(
            FileSizeRule(
                enabled=True,
                max_bytes=int(size_settings.get("max_bytes", 104857600)),
            )
        )

    return rules
