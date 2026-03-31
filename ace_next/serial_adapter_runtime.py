
from __future__ import annotations
from typing import Any
from ace_next.serial_continuity_engine import build_serial_continuity

def run_serial_adapter(input_payload: dict[str, Any]) -> dict[str, Any]:
    result = build_serial_continuity(**(input_payload or {}))

    return {
        "ok": True,
        "state": "serial_adapter_ready",
        "data": result,
        "meta": {
            "source": "serial_continuity_engine",
            "adapter": "runtime_level"
        }
    }
