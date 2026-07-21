"""Glob-style path ignore matching for shared ``rule_ignore`` settings."""

from __future__ import annotations

import fnmatch
from typing import Any


def normalize_rule_ignore(values: list[str] | None) -> list[str]:
    """Coerce ignore patterns to non-empty strings; preserve order."""
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        pattern = str(value).strip()
        if pattern:
            normalized.append(pattern)
    return normalized


def normalize_path_for_match(path: str) -> str:
    """Normalize separators for matching; do not change case."""
    normalized = str(path).replace("\\", "/")
    if len(normalized) > 1 and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized


def path_is_ignored(path: str, patterns: list[str]) -> bool:
    """Return True if *path* matches any ignore pattern."""
    if not patterns:
        return False
    normalized_path = normalize_path_for_match(path)
    for pattern in patterns:
        if _path_matches_pattern(normalized_path, normalize_path_for_match(pattern)):
            return True
    return False


def _path_matches_pattern(path: str, pattern: str) -> bool:
    if "**" in pattern:
        return _match_with_doublestar(path, pattern)
    return fnmatch.fnmatchcase(path, pattern)


def _match_with_doublestar(path: str, pattern: str) -> bool:
    """Match globs that include ``**`` (directory-spanning)."""
    if pattern == "**":
        return True
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        if path == prefix or path.startswith(prefix + "/"):
            return True
    if pattern.startswith("**/"):
        suffix = pattern[3:]
        if _match_with_doublestar(path, suffix):
            return True
        path_parts = path.split("/")
        for index in range(len(path_parts)):
            candidate = "/".join(path_parts[index:])
            if _match_with_doublestar(candidate, suffix):
                return True
        return False

    parts = pattern.split("/")
    return _match_segments(path.split("/"), parts)


def _match_segments(path_parts: list[str], pattern_parts: list[str]) -> bool:
    if not pattern_parts:
        return not path_parts
    head, *tail = pattern_parts
    if head == "**":
        if not tail:
            return True
        for index in range(len(path_parts) + 1):
            if _match_segments(path_parts[index:], tail):
                return True
        return False
    if not path_parts:
        return False
    if not fnmatch.fnmatchcase(path_parts[0], head):
        return False
    return _match_segments(path_parts[1:], tail)


def common_filter_kwargs(settings: dict[str, Any]) -> dict[str, Any]:
    """Shared ``apply_to_extensions`` + ``rule_ignore`` kwargs for ``from_settings``."""
    return {
        "apply_to_extensions": settings.get("apply_to_extensions"),
        "rule_ignore": settings.get("rule_ignore"),
    }
