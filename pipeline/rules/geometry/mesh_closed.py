from __future__ import annotations

from typing import Any

from pipeline.core.context import ValidationContext
from pipeline.core.metadata import AssetMetadata
from pipeline.rules.models import RuleCategory, RuleResult, Severity
from pipeline.rules.path_ignore import common_filter_kwargs, normalize_rule_ignore
from pipeline.rules.validation_rule import ValidationRule, normalize_extensions
from pipeline.unreal.env import UNREAL_AVAILABLE, unreal


class MeshClosedRule(ValidationRule):
    """Unreal-only: Static Mesh closedness via DynamicMesh queries."""

    name = "mesh_closed"
    category = RuleCategory.GEOMETRY

    def __init__(
        self,
        enabled: bool,
        require_closed: bool,
        apply_to_extensions: list[str] | None = None,
        rule_ignore: list[str] | None = None,
    ) -> None:
        self.enabled = enabled
        self.require_closed = require_closed
        self.apply_to_extensions = normalize_extensions(apply_to_extensions)
        self.rule_ignore = normalize_rule_ignore(rule_ignore)

    @classmethod
    def from_settings(cls, settings: dict[str, Any]) -> MeshClosedRule:
        return cls(
            enabled=True,
            require_closed=bool(settings.get("require_closed", True)),
            **common_filter_kwargs(settings),
        )

    def validate(
        self, asset: AssetMetadata, ctx: ValidationContext
    ) -> list[RuleResult]:
        if not UNREAL_AVAILABLE or unreal is None:
            return [self.make_skipped("Unreal Engine not available.")]

        loaded = ctx.load_uobject(asset.path)
        queried = _query_closedness(loaded)
        if queried is None:
            return []

        is_closed, border_edges, border_loops, ambiguous = queried
        results = [self._closedness_result(is_closed, border_edges, border_loops)]
        if ambiguous:
            results.append(self._ambiguous_warning())
        return results

    def _closedness_result(
        self,
        is_closed: bool,
        border_edges: int,
        border_loops: int,
    ) -> RuleResult:
        if is_closed:
            return RuleResult(
                severity=Severity.INFO,
                rule=self.name,
                category=self.category,
                message="Mesh is closed",
            )

        counts = (
            f"open border edges={border_edges}, open border loops={border_loops}"
        )
        if self.require_closed:
            return RuleResult(
                severity=Severity.ERROR,
                rule=self.name,
                category=self.category,
                message=f"Mesh is not closed ({counts})",
            )
        return RuleResult(
            severity=Severity.INFO,
            rule=self.name,
            category=self.category,
            message=f"Mesh is open ({counts})",
        )

    def _ambiguous_warning(self) -> RuleResult:
        return RuleResult(
            severity=Severity.WARNING,
            rule=self.name,
            category=self.category,
            message="Ambiguous open-border-loop topology detected",
        )


def _query_closedness(loaded: Any) -> tuple[bool, int, int, bool] | None:
    assert unreal is not None
    if loaded is None or not isinstance(loaded, unreal.StaticMesh):
        return None

    mesh = _copy_to_dynamic_mesh(loaded)
    if mesh is None:
        return None
    return _read_closedness(mesh)


def _copy_to_dynamic_mesh(static_mesh: Any) -> Any | None:
    assert unreal is not None
    dynamic_mesh = unreal.DynamicMesh()
    copy_options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    requested_lod = unreal.GeometryScriptMeshReadLOD()

    try:
        copy_result = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(
            static_mesh,
            dynamic_mesh,
            copy_options,
            requested_lod,
        )
    except Exception as exc:
        unreal.log_warning(f"mesh_closed: failed to copy static mesh: {exc}")
        return None

    mesh = dynamic_mesh
    outcome = None
    if isinstance(copy_result, tuple):
        if copy_result:
            maybe_mesh = copy_result[0]
            if maybe_mesh is not None:
                mesh = maybe_mesh
        if len(copy_result) > 1:
            outcome = copy_result[1]
    elif copy_result is not None and not isinstance(copy_result, bool):
        mesh = copy_result

    if not _copy_outcome_ok(outcome) and outcome is not None:
        unreal.log_warning(f"mesh_closed: copy outcome not successful: {outcome}")
        return None
    return mesh


def _read_closedness(mesh: Any) -> tuple[bool, int, int, bool] | None:
    assert unreal is not None
    try:
        queries = unreal.GeometryScript_MeshQueries
        is_closed = bool(queries.get_is_closed_mesh(mesh))
        border_edges = int(queries.get_num_open_border_edges(mesh))
        border_loops, ambiguous = _unpack_border_loops(
            queries.get_num_open_border_loops(mesh)
        )
    except Exception as exc:
        unreal.log_warning(f"mesh_closed: query failed: {exc}")
        return None
    return is_closed, border_edges, border_loops, ambiguous


def _copy_outcome_ok(outcome: Any) -> bool:
    assert unreal is not None
    pins = getattr(unreal, "GeometryScriptOutcomePins", None)
    if pins is None:
        return outcome is None or bool(outcome)
    success_value = getattr(pins, "SUCCESS", None)
    if success_value is not None and outcome == success_value:
        return True
    return outcome is True or outcome is None


def _unpack_border_loops(raw: Any) -> tuple[int, bool]:
    if isinstance(raw, tuple):
        if len(raw) >= 2:
            return int(raw[0]), bool(raw[1])
        if len(raw) == 1:
            return int(raw[0]), False
    return int(raw), False
