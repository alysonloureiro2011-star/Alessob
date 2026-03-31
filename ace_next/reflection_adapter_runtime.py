from __future__ import annotations
from typing import Any
from ace_next.reflection_engine import ReflectionEngine


def run_reflection_adapter(input_payload: dict[str, Any]) -> dict[str, Any]:
    engine = ReflectionEngine()
    result = engine.run(**(input_payload or {})) or {}

    return {
        "ok": True,
        "state": "reflection_adapter_ready",
        "data": result,
        "meta": {
            "source": "reflection_engine",
            "adapter": "runtime_level"
        }
    }
