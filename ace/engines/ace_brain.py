import json
import random
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ace.engines.director_engine import choose_style, choose_content_type

# ==========================================================
# ACE Ω — ACE BRAIN
# memória + decisão + score adaptativo
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

ACE_BRAIN_MEMORY_PATH = MEMORY_DIR / "ace_brain_memory.json"


# ==========================================================
# CONFIG
# ==========================================================

DEFAULT_BRAIN_MEMORY = {
    "version": 1,
    "created_at": None,
    "updated_at": None,
    "history": [],
    "trend_scores": {},
    "style_scores": {},
    "content_type_scores": {},
    "hour_scores": {},
    "totals": {
        "posts_registered": 0
    }
}


# ==========================================================
# MEMORY
# ==========================================================

def _utc_now_iso() -> str:
    return datetime.datetime.utcnow().isoformat()


def _today_hour_utc() -> int:
    return datetime.datetime.utcnow().hour


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _normalize_key(value: Optional[str], fallback: str) -> str:
    value = (value or "").strip().lower()
    return value if value else fallback


def _load_memory() -> Dict[str, Any]:
    if ACE_BRAIN_MEMORY_PATH.exists():
        try:
            data = json.loads(ACE_BRAIN_MEMORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return _merge_defaults(data)
        except Exception:
            pass

    data = DEFAULT_BRAIN_MEMORY.copy()
    data["created_at"] = _utc_now_iso()
    data["updated_at"] = _utc_now_iso()
    _save_memory(data)
    return data


def _merge_defaults(data: Dict[str, Any]) -> Dict[str, Any]:
    merged = {
        "version": data.get("version", 1),
        "created_at": data.get("created_at") or _utc_now_iso(),
        "updated_at": data.get("updated_at") or _utc_now_iso(),
        "history": data.get("history", []),
        "trend_scores": data.get("trend_scores", {}),
        "style_scores": data.get("style_scores", {}),
        "content_type_scores": data.get("content_type_scores", {}),
        "hour_scores": data.get("hour_scores", {}),
        "totals": data.get("totals", {"posts_registered": 0}),
    }

    if "posts_registered" not in merged["totals"]:
        merged["totals"]["posts_registered"] = 0

    return merged


def _save_memory(memory: Dict[str, Any]) -> None:
    memory["updated_at"] = _utc_now_iso()
