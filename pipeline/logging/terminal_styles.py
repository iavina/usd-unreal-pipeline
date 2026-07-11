"""Terminal icons, color, and column formatting for validation output."""

import os
import sys
from io import StringIO

from rich.console import Console
from rich.text import Text

from pipeline.rules.models import Severity

PASS_ICON = "\u2705"
FAIL_ICON = "\u274c"
PASS_LABEL = "[PASS]"
FAIL_LABEL = "[FAILED]"
SUMMARY_TITLE = "Validation Summary"
SUMMARY_LABELS = ("Files processed", "Passed", "Failed", "Failed rule checks")


def color_enabled() -> bool:
    """Return whether styled terminal output should be used."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return Console().color_system is not None


def _to_ansi(text: str, style: str) -> str:
    buffer = StringIO()
    console = Console(
        file=buffer,
        force_terminal=True,
        color_system="standard",
        highlight=False,
    )
    console.print(Text(text, style=style), end="", soft_wrap=False)
    return buffer.getvalue()


def status_text(passed: bool) -> str:
    """Return the visible status tag text without ANSI styling."""
    label = PASS_LABEL if passed else FAIL_LABEL
    if not color_enabled():
        return label
    icon = PASS_ICON if passed else FAIL_ICON
    return f"{icon} {label}"


def status_column_width() -> int:
    """Return fixed visible width for the status column."""
    return max(len(status_text(True)), len(status_text(False)))


def format_status_tag(passed: bool) -> str:
    """Return a padded, optionally styled status tag for one file line."""
    text = status_text(passed)
    padded = f"{text:<{status_column_width()}}"
    if not color_enabled():
        return padded
    color = "green" if passed else "red"
    return _to_ansi(padded, color)


def format_severity_label(severity: Severity) -> str:
    """Return a severity tag; color error/warning only when styling is enabled."""
    label = f"({severity.value})"
    if not color_enabled():
        return label
    if severity == Severity.ERROR:
        return _to_ansi(label, "red")
    if severity == Severity.WARNING:
        return _to_ansi(label, "yellow")
    return label


def format_summary_header() -> str:
    """Return the run summary section title."""
    if not color_enabled():
        return SUMMARY_TITLE
    return _to_ansi(SUMMARY_TITLE, "bold")


def format_summary_rows(rows: list[tuple[str, int]]) -> list[str]:
    """Return column-aligned summary metric rows."""
    label_width = max(len(label) for label, _ in rows)
    value_width = max(3, max(len(str(value)) for _, value in rows))
    return [
        f"{label:<{label_width}}  {value:>{value_width}}"
        for label, value in rows
    ]
