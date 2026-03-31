
from __future__ import annotations
from typing import Any
from ace_next.visual_hierarchy_gate import evaluate_visual_hierarchy_gate

def run_visual_gate_adapter(input_payload: dict[str, Any]) -> dict[str, Any]:
    result = evaluate_visual_hierarchy_gate(input_payload or {})

    return {
        "ok": True,
        "state": "visual_gate_adapter_ready",
        "data": result,
        "meta": {
            "source": "visual_hierarchy_gate",
            "adapter": "runtime_level"
        }
    }
