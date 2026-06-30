"""Run enabled validation rules and aggregate per-file results."""

from pathlib import Path

from pipeline.logging import FailedRule, FileValidationResult, Severity
from pipeline.rules import ValidationRule


def validate_files(
    files: list[Path], rules: list[ValidationRule]
) -> list[FileValidationResult]:
    """Apply all enabled rules to every file and aggregate per-file results."""
    results: list[FileValidationResult] = []

    for file in files:
        failed_rules: list[FailedRule] = []

        for rule in rules:
            entries = rule.validate(file)
            for entry in entries:
                if entry.severity == Severity.ERROR:
                    failed_rules.append(
                        FailedRule(rule=entry.rule, message=entry.message)
                    )

        results.append(
            FileValidationResult(
                file=file,
                passed=len(failed_rules) == 0,
                failed_rules=failed_rules,
            )
        )

    return results
