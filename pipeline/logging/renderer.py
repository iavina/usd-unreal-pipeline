"""Render validation results into stable, human-readable terminal output."""

from collections import defaultdict

import typer

from pipeline.logging.terminal_styles import (
    SUMMARY_LABELS,
    format_severity_label,
    format_status_tag,
    format_summary_header,
    format_summary_rows,
)
from pipeline.rules.models import Severity
from pipeline.validation.models import FileValidationResult

GAP = " " * 4
RULE_INDENT = " " * 10
CATEGORY_SUMMARY_TITLE = "By Category"


def render_file_result(result: FileValidationResult) -> list[str]:
    """Render one file's pass or failed block as terminal lines."""
    status_tag = format_status_tag(result.passed)
    lines = [f"{status_tag}{GAP}{result.file}"]

    for rule_result in result.rule_results:
        severity = format_severity_label(rule_result.severity)
        lines.append(
            f"{RULE_INDENT}- [{rule_result.category.value}] "
            f"{rule_result.rule} {severity}: "
            f"{rule_result.message}"
        )

    if result.rule_results:
        lines.append("")

    return lines


def render_category_summary(results: list[FileValidationResult]) -> list[str]:
    """Render per-category checks/errors/warnings for categories with results."""
    checks: dict[str, int] = defaultdict(int)
    errors: dict[str, int] = defaultdict(int)
    warnings: dict[str, int] = defaultdict(int)

    for result in results:
        for rule_result in result.rule_results:
            key = rule_result.category.value
            checks[key] += 1
            if rule_result.severity == Severity.ERROR:
                errors[key] += 1
            elif rule_result.severity == Severity.WARNING:
                warnings[key] += 1

    if not checks:
        return []

    lines = ["", CATEGORY_SUMMARY_TITLE]
    for category in sorted(checks):
        lines.append(
            f"{category}  checks={checks[category]}  "
            f"errors={errors[category]}  warnings={warnings[category]}"
        )
    return lines


def render_summary(results: list[FileValidationResult], file_count: int) -> list[str]:
    """Render a whole-run summary after per-file results."""
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count
    failed_rule_checks = sum(
        len(result.failed_rule_results) for result in results
    )

    rows = [
        (SUMMARY_LABELS[0], file_count),
        (SUMMARY_LABELS[1], passed_count),
        (SUMMARY_LABELS[2], failed_count),
        (SUMMARY_LABELS[3], failed_rule_checks),
    ]

    return [
        "",
        format_summary_header(),
        *format_summary_rows(rows),
        *render_category_summary(results),
        "",
    ]


def render_results(results: list[FileValidationResult], file_count: int) -> None:
    """Print structured per-file validation output and a run summary."""
    for result in results:
        for line in render_file_result(result):
            typer.echo(line)
    for line in render_summary(results, file_count):
        typer.echo(line)
