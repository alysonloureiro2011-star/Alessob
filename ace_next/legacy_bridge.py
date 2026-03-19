from __future__ import annotations

from typing import Any


def run_legacy_pipeline(trend: str | None = None) -> dict[str, Any]:
    from ace.pipeline.run_pipeline import run_pipeline
    return run_pipeline(trend=trend)


def get_legacy_memory_summary() -> dict[str, Any]:
    from ace.engines.episodic_memory_engine import build_memory_summary
    return build_memory_summary()
