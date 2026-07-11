"""Run enabled validation rules and aggregate per-file results."""

from pathlib import Path

from pipeline.rules import ValidationRule
from pipeline.validation.models import FileValidationResult


def validate_files(
    files: list[Path], rules: list[ValidationRule]
) -> list[FileValidationResult]:
    """Apply applicable enabled rules to every file and aggregate per-file results."""
    results: list[FileValidationResult] = []

    for file in files:
        rule_results = []

        for rule in rules:
            if not rule.applies_to(file):
                continue
            rule_results.extend(rule.validate(file))

        results.append(
            FileValidationResult(
                file=file,
                rule_results=rule_results,
            )
        )

    return results
