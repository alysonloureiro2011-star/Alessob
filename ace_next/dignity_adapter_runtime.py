
from __future__ import annotations
from typing import Any
from ace_next.brand_dignity_score import evaluate_brand_dignity_score

def run_dignity_adapter(input_payload: dict[str, Any]) -> dict[str, Any]:
    result = evaluate_brand_dignity_score(input_payload or {})

    return {
        "ok": True,
        "state": "dignity_adapter_ready",
        "data": result,
        "meta": {
            "source": "brand_dignity_score",
            "adapter": "runtime_level"
        }
    }
