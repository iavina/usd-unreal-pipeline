"""Run enabled validation rules and aggregate per-asset results."""

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.core.models import AssetValidationResult
from pipeline.rules import ValidationRule


def validate_assets(
    assets: list[AssetMetadata],
    rules: list[ValidationRule],
    ctx: ValidationContext,
) -> list[AssetValidationResult]:
    """Apply applicable rules to every asset and aggregate results."""
    results: list[AssetValidationResult] = []

    for asset in assets:
        rule_results = []

        for rule in rules:
            if not rule.applies_to(asset, ctx):
                continue
            rule_results.extend(rule.validate(asset, ctx))

        results.append(
            AssetValidationResult(
                asset=asset,
                rule_results=rule_results,
            )
        )

    return results
