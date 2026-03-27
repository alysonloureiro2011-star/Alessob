from __future__ import annotations

from typing import Any


def adapt_legacy_mission_decision(value: dict[str, Any] | None) -> dict[str, Any]:
    value = dict(value or {})
    return {
        "trend": value.get("trend"),
        "style": value.get("style"),
        "content_type": value.get("content_type"),
        "goal": value.get("goal"),
        "confidence": value.get("confidence"),
        "raw": value,
    }


def adapt_legacy_publish_result(value: dict[str, Any] | None) -> dict[str, Any]:
    value = dict(value or {})
    return {
        "publish_status": value.get("publish_status"),
        "receipt_id": value.get("receipt_id"),
        "media_id": value.get("media_id"),
        "permalink": value.get("permalink"),
        "raw": value,
    }


def adapt_legacy_visual(value: dict[str, Any] | None) -> dict[str, Any]:
    value = dict(value or {})
    return {
        "visual_score": value.get("final_score"),
        "approved": value.get("approved"),
        "raw": value,
    }


def adapter_snapshot() -> dict[str, Any]:
    return {
        "ok": True,
        "adapters": [
            "adapt_legacy_mission_decision",
            "adapt_legacy_publish_result",
            "adapt_legacy_visual",
        ],
        "mode": "compatibility_layer",
    }
