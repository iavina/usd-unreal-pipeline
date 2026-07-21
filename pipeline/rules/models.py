"""Rule-domain types: categories, severities, and per-rule results."""

from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class RuleCategory(str, Enum):
    FILESYSTEM = "filesystem"
    GEOMETRY = "geometry"
    TEXTURES = "textures"
    UNREAL = "unreal"
    MATERIALS = "materials"


@dataclass(frozen=True)
class RuleResult:
    severity: Severity
    rule: str
    category: RuleCategory
    message: str
    skipped: bool = False
