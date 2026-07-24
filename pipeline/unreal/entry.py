"""Unreal editor entrypoint for shared validation runs."""

from __future__ import annotations

from pathlib import Path

from pipeline.config.loader import load_config
from pipeline.core.metadata import AssetMetadata
from pipeline.core.runner import validate_assets
from pipeline.report.formatter import format_results
from pipeline.rules import build_rules
from pipeline.unreal.context import UnrealContext
from pipeline.unreal.output import emit_lines
from pipeline.unreal.runtime import import_unreal


def run_validation(
    config_path: str | Path | None = None,
    content_root: str | None = None,
    asset_paths: list[str] | None = None,
) -> bool:
    """Validate assets with enabled rules.

    Scope:
    - If ``asset_paths`` is not ``None``, validate only those object paths
      (skips recursive discovery). When both ``asset_paths`` and
      ``content_root`` are given, ``asset_paths`` wins for target selection.
    - Otherwise discover recursively under ``content_root``, else config
      ``host.content_root``, else the built-in default ``/Game/ExampleContent``.

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

    if asset_paths is not None:
        assets = _resolve_asset_paths(ctx, asset_paths)
        if not assets:
            import_unreal().log_warning(
                "WARNING: No resolvable assets in asset_paths; nothing to validate"
            )
            return True
    else:
        assets = ctx.get_assets()

    results = validate_assets(assets, rules, ctx)
    rule_names = [f"{rule.category.value}/{rule.name}" for rule in rules]
    lines = format_results(results, len(assets), rule_names=rule_names)
    emit_lines(lines)
    return all(result.passed for result in results)


def _resolve_asset_paths(
    ctx: UnrealContext,
    asset_paths: list[str],
) -> list[AssetMetadata]:
    unreal = import_unreal()
    resolved: list[AssetMetadata] = []
    for raw in asset_paths:
        path = raw.strip()
        if not path:
            continue
        meta = ctx.get_asset_metadata(path)
        if meta is None:
            unreal.log_warning(f"WARNING: Could not resolve asset path: {path}")
            continue
        resolved.append(meta)
    return resolved
