"""No-arg entry for Unreal Editor → Execute Python Script.

Validates assets under /Game/ExampleContent using the shared pipeline host.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Unreal's Python does not use this repo's venv, so `pipeline` is not installed.
# Add the repo root (parent of scripts/) to sys.path so `import pipeline...` works.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline.unreal import run_validation

_CONFIG = Path(__file__).with_name("unreal_validate_config.json")
run_validation(config_path=_CONFIG)
