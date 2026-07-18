"""Format validation results as shared text lines."""

from collections import defaultdict
from types import ModuleType, SimpleNamespace
from typing import Any

from pipeline.core.models import AssetValidationResult
from pipeline.report import styles as default_styles
from pipeline.rules.models import Severity

GAP = " " * 4
RULE_INDENT = " " * 10
CATEGORY_SUMMARY_TITLE = "By Category"

Styles = ModuleType | SimpleNamespace | Any


def format_asset_result(
    result: AssetValidationResult,
    styles: Styles = default_styles,
) -> list[str]:
    lines = [f"{styles.format_status_tag(result.passed)}{GAP}{result.asset.path}"]

    for rule_result in result.rule_results:
        if rule_result.skipped:
            label = getattr(styles, "SKIPPED_LABEL", "(skipped)")
        else:
            label = styles.format_severity_label(rule_result.severity)
        lines.append(
            f"{RULE_INDENT}- [{rule_result.category.value}] "
            f"{rule_result.rule} {label}: "
            f"{rule_result.message}"
        )

    if result.rule_results:
        lines.append("")

    return lines


def format_category_summary(results: list[AssetValidationResult]) -> list[str]:
    checks: dict[str, int] = defaultdict(int)
    errors: dict[str, int] = defaultdict(int)
    warnings: dict[str, int] = defaultdict(int)
    skipped: dict[str, int] = defaultdict(int)

    for result in results:
        for rule_result in result.rule_results:
            key = rule_result.category.value
            checks[key] += 1
            if rule_result.skipped:
                skipped[key] += 1
            elif rule_result.severity == Severity.ERROR:
                errors[key] += 1
            elif rule_result.severity == Severity.WARNING:
                warnings[key] += 1

    if not checks:
        return []

    lines = ["", CATEGORY_SUMMARY_TITLE]
    for category in sorted(checks):
        lines.append(
            f"{category}  checks={checks[category]}  "
            f"errors={errors[category]}  warnings={warnings[category]}  "
            f"skipped={skipped[category]}"
        )
    return lines


def format_rules_checked(rule_names: list[str]) -> list[str]:
    if not rule_names:
        return []
    lines = ["", default_styles.RULES_CHECKED_TITLE]
    for name in rule_names:
        lines.append(f"  - {name}")
    return lines


def format_summary(
    results: list[AssetValidationResult],
    asset_count: int,
    styles: Styles = default_styles,
    rule_names: list[str] | None = None,
) -> list[str]:
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count
    failed_rule_checks = sum(
        len(result.failed_rule_results) for result in results
    )
    skipped_rule_checks = sum(
        1
        for result in results
        for rule_result in result.rule_results
        if rule_result.skipped
    )

    rows = [
        (styles.SUMMARY_LABELS[0], asset_count),
        (styles.SUMMARY_LABELS[1], passed_count),
        (styles.SUMMARY_LABELS[2], failed_count),
        (styles.SUMMARY_LABELS[3], failed_rule_checks),
        (styles.SUMMARY_LABELS[4], skipped_rule_checks),
    ]

    separator = styles.format_summary_separator()
    return [
        "",
        separator,
        styles.format_summary_header(),
        separator,
        *styles.format_summary_rows(rows),
        *format_rules_checked(rule_names or []),
        *format_category_summary(results),
        "",
    ]


def format_results(
    results: list[AssetValidationResult],
    asset_count: int,
    styles: Styles = default_styles,
    rule_names: list[str] | None = None,
) -> list[str]:
    lines: list[str] = []
    for result in results:
        lines.extend(format_asset_result(result, styles=styles))
    lines.extend(
        format_summary(
            results,
            asset_count,
            styles=styles,
            rule_names=rule_names,
        )
    )
    return lines
