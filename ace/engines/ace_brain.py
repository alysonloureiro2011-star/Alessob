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
    ACE_BRAIN_MEMORY_PATH.write_text(
        json.dumps(memory, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


ACE_BRAIN_MEMORY = _load_memory()


# ==========================================================
# SCORE
# ==========================================================

def compute_performance_score(
    likes: Any = 0,
    comments: Any = 0,
    saves: Any = 0,
    shares: Any = 0,
    reach: Any = 0,
    views: Any = 0,
) -> float:
    """
    Score simples e robusto para o estágio atual do ACE.
    Mantém fórmula compreensível e fácil de ajustar.
    """
    likes = _safe_float(likes)
    comments = _safe_float(comments)
    saves = _safe_float(saves)
    shares = _safe_float(shares)
    reach = _safe_float(reach)
    views = _safe_float(views)

    base = (
        likes * 1.0
        + comments * 2.5
        + saves * 3.5
        + shares * 4.0
    )

    exposure = max(reach, views, 1.0)

    # score relativo + score absoluto pequeno
    relative = (base / exposure) * 1000.0
    absolute = base * 0.05

    return round(relative + absolute, 4)


def _update_score_bucket(bucket: Dict[str, Any], score: float) -> Dict[str, Any]:
    count = int(bucket.get("count", 0)) + 1
    total = _safe_float(bucket.get("total_score", 0.0)) + score
    avg = total / count if count else 0.0

    bucket["count"] = count
    bucket["total_score"] = round(total, 4)
    bucket["avg_score"] = round(avg, 4)
    bucket["last_score"] = round(score, 4)
    bucket["last_updated_at"] = _utc_now_iso()

    return bucket


# ==========================================================
# REGISTRO DE FEEDBACK
# ==========================================================

def register_feedback(
    trend: Optional[str],
    style: Optional[str],
    content_type: Optional[str],
    likes: Any = 0,
    comments: Any = 0,
    saves: Any = 0,
    shares: Any = 0,
    reach: Any = 0,
    views: Any = 0,
    posted_hour: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Registra performance de um post e atualiza memória do ACE Brain.
    """
    memory = ACE_BRAIN_MEMORY

    trend_key = _normalize_key(trend, "unknown_trend")
    style_key = _normalize_key(style, "unknown_style")
    content_key = _normalize_key(content_type, "unknown_content_type")
    hour_key = str(posted_hour if posted_hour is not None else _today_hour_utc())

    score = compute_performance_score(
        likes=likes,
        comments=comments,
        saves=saves,
        shares=shares,
        reach=reach,
        views=views,
    )

    trend_bucket = memory["trend_scores"].get(trend_key, {})
    style_bucket = memory["style_scores"].get(style_key, {})
    content_bucket = memory["content_type_scores"].get(content_key, {})
    hour_bucket = memory["hour_scores"].get(hour_key, {})

    memory["trend_scores"][trend_key] = _update_score_bucket(trend_bucket, score)
    memory["style_scores"][style_key] = _update_score_bucket(style_bucket, score)
    memory["content_type_scores"][content_key] = _update_score_bucket(content_bucket, score)
    memory["hour_scores"][hour_key] = _update_score_bucket(hour_bucket, score)

    history_item = {
        "timestamp": _utc_now_iso(),
        "trend": trend_key,
        "style": style_key,
        "content_type": content_key,
        "posted_hour": int(hour_key),
        "likes": _safe_float(likes),
        "comments": _safe_float(comments),
        "saves": _safe_float(saves),
        "shares": _safe_float(shares),
        "reach": _safe_float(reach),
        "views": _safe_float(views),
        "score": score,
        "extra": extra or {},
    }

    memory["history"].append(history_item)
    memory["history"] = memory["history"][-300:]
    memory["totals"]["posts_registered"] = int(memory["totals"].get("posts_registered", 0)) + 1

    _save_memory(memory)

    return {
        "ok": True,
        "score": score,
        "trend": trend_key,
        "style": style_key,
        "content_type": content_key,
        "posted_hour": int(hour_key),
    }


# ==========================================================
# DECISÃO
# ==========================================================

def _get_avg_score(score_map: Dict[str, Any], key: str) -> float:
    item = score_map.get(key, {})
    return _safe_float(item.get("avg_score", 0.0))


def _pick_best_hour() -> int:
    hour_scores = ACE_BRAIN_MEMORY.get("hour_scores", {})
    if not hour_scores:
        return _today_hour_utc()

    best_hour = None
    best_score = -999999.0

    for hour_str, data in hour_scores.items():
        avg_score = _safe_float(data.get("avg_score", 0.0))
        count = int(data.get("count", 0))

        # pequeno bônus de confiança por recorrência
        weighted_score = avg_score + min(count * 0.15, 2.0)

        if weighted_score > best_score:
            best_score = weighted_score
            best_hour = hour_str

    try:
        return int(best_hour)
    except Exception:
        return _today_hour_utc()


def _score_candidate_plan(trend: str, style: str, content_type: str) -> float:
    trend_score = _get_avg_score(ACE_BRAIN_MEMORY.get("trend_scores", {}), trend)
    style_score = _get_avg_score(ACE_BRAIN_MEMORY.get("style_scores", {}), style)
    content_score = _get_avg_score(ACE_BRAIN_MEMORY.get("content_type_scores", {}), content_type)

    # pesos simples e transparentes
    return round(
        trend_score * 0.45
        + style_score * 0.30
        + content_score * 0.25,
        4
    )


def build_brain_plan(
    candidate_trends: Optional[List[str]] = None,
    fallback_trend: str = "disciplina e prosperidade",
) -> Dict[str, Any]:
    """
    Decide o melhor plano usando memória histórica + heurísticas existentes.
    Não depende de banco.
    Não quebra o resto do projeto.
    """
    candidate_trends = candidate_trends or [fallback_trend]
    candidate_trends = [t for t in candidate_trends if str(t).strip()]

    if not candidate_trends:
        candidate_trends = [fallback_trend]

    ranked_plans = []

    for trend in candidate_trends:
        trend_key = _normalize_key(trend, fallback_trend)
        style = choose_style(trend_key)
        content_type = choose_content_type(trend_key)
        plan_score = _score_candidate_plan(trend_key, style, content_type)

        ranked_plans.append({
            "trend": trend_key,
            "style": style,
            "content_type": content_type,
            "score": plan_score,
        })

    ranked_plans.sort(key=lambda x: x["score"], reverse=True)
    best = ranked_plans[0]

    return {
        "trend": best["trend"],
        "style": best["style"],
        "content_type": best["content_type"],
        "score": best["score"],
        "recommended_hour_utc": _pick_best_hour(),
        "ranked_candidates": ranked_plans[:5],
        "memory_posts_registered": int(
            ACE_BRAIN_MEMORY.get("totals", {}).get("posts_registered", 0)
        ),
    }


# ==========================================================
# STATUS / DEBUG
# ==========================================================

def get_brain_status() -> Dict[str, Any]:
    memory = ACE_BRAIN_MEMORY

    return {
        "memory_path": str(ACE_BRAIN_MEMORY_PATH),
        "posts_registered": int(memory.get("totals", {}).get("posts_registered", 0)),
        "history_size": len(memory.get("history", [])),
        "known_trends": len(memory.get("trend_scores", {})),
        "known_styles": len(memory.get("style_scores", {})),
        "known_content_types": len(memory.get("content_type_scores", {})),
        "recommended_hour_utc": _pick_best_hour(),
        "updated_at": memory.get("updated_at"),
    }
