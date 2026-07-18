"""Shared status labels; CLI may use the ``ansi`` helpers for color."""

from types import SimpleNamespace

from pipeline.rules.models import Severity

PASS_LABEL = "✅ [PASS]"
FAIL_LABEL = "❌ [FAILED]"
SUMMARY_TITLE = "Validation Summary"
SUMMARY_SEPARATOR = "-" * len(SUMMARY_TITLE)
SUMMARY_LABELS = (
    "Assets processed",
    "Passed",
    "Failed",
    "Failed rule checks",
    "Skipped rule checks",
)
RULES_CHECKED_TITLE = "Rules checked"
SKIPPED_LABEL = "(skipped)"

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"


def format_status_tag(passed: bool) -> str:
    return PASS_LABEL if passed else FAIL_LABEL


def format_severity_label(severity: Severity) -> str:
    return f"({severity.value})"


def format_summary_header() -> str:
    return SUMMARY_TITLE


def format_summary_separator() -> str:
    return SUMMARY_SEPARATOR


def format_summary_rows(rows: list[tuple[str, int]]) -> list[str]:
    label_width = max(len(label) for label, _ in rows)
    value_width = max(3, max(len(str(value)) for _, value in rows))
    return [
        f"{label:<{label_width}}  {value:>{value_width}}"
        for label, value in rows
    ]


def _ansi_status_tag(passed: bool) -> str:
    label = format_status_tag(passed)
    color = GREEN if passed else RED
    return f"{color}{label}{RESET}"


def _ansi_severity_label(severity: Severity) -> str:
    label = format_severity_label(severity)
    if severity == Severity.ERROR:
        return f"{RED}{label}{RESET}"
    if severity == Severity.WARNING:
        return f"{YELLOW}{label}{RESET}"
    return label


def _ansi_summary_header() -> str:
    return f"{BOLD}{format_summary_header()}{RESET}"


ansi = SimpleNamespace(
    SUMMARY_LABELS=SUMMARY_LABELS,
    SKIPPED_LABEL=SKIPPED_LABEL,
    format_status_tag=_ansi_status_tag,
    format_severity_label=_ansi_severity_label,
    format_summary_header=_ansi_summary_header,
    format_summary_separator=format_summary_separator,
    format_summary_rows=format_summary_rows,
)
