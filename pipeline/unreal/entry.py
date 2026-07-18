"""Unreal editor entrypoint for shared validation runs."""

from __future__ import annotations

from pathlib import Path

from pipeline.config.loader import load_config
from pipeline.core.runner import validate_assets
from pipeline.report.formatter import format_results
from pipeline.rules import build_rules
from pipeline.unreal.context import UnrealContext
from pipeline.unreal.output import emit_lines
from pipeline.unreal.runtime import import_unreal


def run_validation(
    config_path: str | Path | None = None,
    content_root: str | None = None,
) -> bool:
    """Discover assets and validate with enabled rules.

    Discovery root comes from ``content_root``, else config ``host.content_root``,
    else the built-in default ``/Game/ExampleContent``.

    Returns True when every asset passes (no error-severity results).
    """
    resolved_config: Path | None = None
    if config_path is not None:
        resolved_config = Path(config_path)
        if not resolved_config.is_file():
            raise FileNotFoundError(f"Config file not found: {resolved_config}")

    pipeline_config = load_config(resolved_config)
    scan_root = content_root or pipeline_config.content_root
    ctx = UnrealContext(asset_path=scan_root)

    rules = build_rules(pipeline_config)

    if not rules:
        import_unreal().log_warning("WARNING: No validation rules enabled")
        return True

    assets = ctx.get_assets()
    results = validate_assets(assets, rules, ctx)
    rule_names = [f"{rule.category.value}/{rule.name}" for rule in rules]
    lines = format_results(results, len(assets), rule_names=rule_names)
    emit_lines(lines)
    return all(result.passed for result in results)
