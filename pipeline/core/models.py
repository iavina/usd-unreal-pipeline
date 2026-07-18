"""Result types used by the runner."""

from dataclasses import dataclass, field

from pipeline.core.metadata import AssetMetadata
from pipeline.rules.models import RuleResult, Severity


@dataclass
class AssetValidationResult:
    asset: AssetMetadata
    rule_results: list[RuleResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(result.severity != Severity.ERROR for result in self.rule_results)

    @property
    def failed_rule_results(self) -> list[RuleResult]:
        return [
            result
            for result in self.rule_results
            if result.severity == Severity.ERROR
        ]
