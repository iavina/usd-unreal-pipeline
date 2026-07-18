"""Emit shared result lines through Unreal log channels.

Same text as CLI (emoji, no ANSI). Color comes from Unreal's Error/Warning
channels — the Output Log cannot interpret ANSI escape codes.
"""

from __future__ import annotations

from pipeline.report import styles as shared_styles
from pipeline.unreal.runtime import import_unreal


def emit_lines(lines: list[str]) -> None:
    unreal = import_unreal()
    for line in lines:
        if not line:
            continue
        if shared_styles.FAIL_LABEL in line or "(error)" in line:
            unreal.log_error(line)
        elif "(warning)" in line or line.startswith("WARNING"):
            unreal.log_warning(line)
        else:
            unreal.log(line)
