"""Render validation results into stable, human-readable terminal output."""

import typer

from pipeline.logging.models import FileValidationResult

STATUS_WIDTH = 6
GAP = " " * 4
FAILED_RULE_INDENT = " " * 10


def render_file_result(result: FileValidationResult) -> list[str]:
    """Render one file's pass or failed block as terminal lines."""
    status = "PASS" if result.passed else "FAILED"
    lines = [f"{status:<{STATUS_WIDTH}}{GAP}{result.file}"]

    if not result.passed:
        for failed_rule in result.failed_rules:
            lines.append(
                f"{FAILED_RULE_INDENT}- {failed_rule.rule}: {failed_rule.message}"
            )
        lines.append("")

    return lines


def render_summary(
    file_count: int, passed_count: int, failed_count: int
) -> tuple[str, str]:
    """Render opening and closing run summaries."""
    header = f"Files found: {file_count}"
    footer = f"Passed: {passed_count}  Failed: {failed_count}"
    return header, footer


def render_results(results: list[FileValidationResult], file_count: int) -> None:
    """Print structured per-file validation output."""
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count
    header, footer = render_summary(file_count, passed_count, failed_count)

    typer.echo(header)
    for result in results:
        for line in render_file_result(result):
            typer.echo(line)
    typer.echo(footer)
