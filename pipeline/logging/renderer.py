"""Render validation results into stable, human-readable terminal output."""

import typer

from pipeline.logging.terminal_styles import (
    SUMMARY_LABELS,
    format_status_tag,
    format_summary_header,
    format_summary_rows,
)
from pipeline.validation.models import FileValidationResult

GAP = " " * 4
FAILED_RULE_INDENT = " " * 10


def render_file_result(result: FileValidationResult) -> list[str]:
    """Render one file's pass or failed block as terminal lines."""
    status_tag = format_status_tag(result.passed)
    lines = [f"{status_tag}{GAP}{result.file}"]

    if not result.passed:
        for failed_rule in result.failed_rule_results:
            lines.append(
                f"{FAILED_RULE_INDENT}- {failed_rule.rule}: {failed_rule.message}"
            )
        lines.append("")

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
        "",
    ]


def render_results(results: list[FileValidationResult], file_count: int) -> None:
    """Print structured per-file validation output and a run summary."""
    for result in results:
        for line in render_file_result(result):
            typer.echo(line)
    for line in render_summary(results, file_count):
        typer.echo(line)
