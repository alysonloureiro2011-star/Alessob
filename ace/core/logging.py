
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

LOG_EVENTS = []
VALID_LEVELS = {"DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"}


def log(level: str, event: str, detail: Any = "") -> Dict[str, Any]:
    normalized = str(level or "INFO").upper()
    if normalized not in VALID_LEVELS:
        normalized = "INFO"
    payload = {
        "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        "level": normalized,
        "event": str(event or "unknown_event"),
        "detail": _normalize_detail(detail),
    }
    LOG_EVENTS.append(payload)
    return payload


def snapshot(limit: int = 100) -> Dict[str, Any]:
    safe_limit = max(1, int(limit))
    return {
        "ok": True,
        "total": len(LOG_EVENTS),
        "events": LOG_EVENTS[-safe_limit:],
    }


def clear_logs() -> None:
    LOG_EVENTS.clear()


def _normalize_detail(detail: Any) -> Any:
    if isinstance(detail, (str, int, float, bool)) or detail is None:
        return detail
    if isinstance(detail, dict):
        return {str(k): _normalize_detail(v) for k, v in detail.items()}
    if isinstance(detail, (list, tuple)):
        return [_normalize_detail(v) for v in detail]
    return str(detail)
