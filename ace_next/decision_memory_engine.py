from __future__ import annotations

from typing import Any

from .runtime_contracts import safe_dict


VALID_DECISION_AXES = {"hook", "format", "style", "timing", "headline", "template"}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_axis(value: Any) -> str:
    axis = _clean_text(value).lower()
    return axis if axis in VALID_DECISION_AXES else "hook"


def _score_from_metrics(metrics: dict[str, Any]) -> float:
    save_rate = float(metrics.get("save_rate") or 0.0)
    share_rate = float(metrics.get("share_rate") or 0.0)
    retention = float(metrics.get("retention") or 0.0)
    replay_proxy = float(metrics.get("replay_proxy") or 0.0)
    return round(
        (save_rate * 0.30) +
        (share_rate * 0.30) +
        (retention * 0.25) +
        (replay_proxy * 0.15),
        4,
    )


def build_decision_memory_entry(
    *,
    axis: str,
    candidate: str,
    metrics: dict[str, Any] | None = None,
    hypothesis: str | None = None,
    content_type: str | None = None,
    trend: str | None = None,
) -> dict[str, Any]:
    metrics = safe_dict(metrics)
    normalized_axis = _normalize_axis(axis)
    candidate_text = _clean_text(candidate) or "unknown_candidate"
    performance_score = _score_from_metrics(metrics)

    if performance_score >= 0.70:
        outcome = "winner"
    elif performance_score >= 0.45:
        outcome = "neutral"
    else:
        outcome = "loser"

    return {
        "ok": True,
        "memory_state": "phase_7_decision_memory_ready",
        "axis": normalized_axis,
        "candidate": candidate_text,
        "hypothesis": _clean_text(hypothesis) or None,
        "content_type": _clean_text(content_type) or None,
        "trend": _clean_text(trend) or None,
        "metrics": {
            "save_rate": float(metrics.get("save_rate") or 0.0),
            "share_rate": float(metrics.get("share_rate") or 0.0),
            "retention": float(metrics.get("retention") or 0.0),
            "replay_proxy": float(metrics.get("replay_proxy") or 0.0),
        },
        "performance_score": performance_score,
        "outcome": outcome,
        "recommended_policy": {
            "repeat": outcome == "winner",
            "downrank": outcome == "loser",
            "keep_collecting": outcome == "neutral",
        },
        "study_alignment": {
            "attention_engineering": True,
            "episodic_memory": True,
            "mab_ready": True,
            "proof_before_claim": True,
        },
    }


def build_decision_memory_summary(
    *,
    entries: list[dict[str, Any]] | None = None,
    preferred_axis: str | None = None,
) -> dict[str, Any]:
    items = [safe_dict(item) for item in (entries or []) if safe_dict(item)]
    normalized_axis = _normalize_axis(preferred_axis or "hook")

    winners = [item for item in items if item.get("outcome") == "winner" and item.get("axis") == normalized_axis]
    losers = [item for item in items if item.get("outcome") == "loser" and item.get("axis") == normalized_axis]

    best_candidate = None
    if winners:
        best_candidate = sorted(
            winners,
            key=lambda item: float(item.get("performance_score") or 0.0),
            reverse=True,
        )[0].get("candidate")

    avoid_candidates = [item.get("candidate") for item in losers[:3] if item.get("candidate")]

    return {
        "ok": True,
        "summary_state": "phase_7_decision_memory_summary_ready",
        "preferred_axis": normalized_axis,
        "best_candidate": best_candidate,
        "avoid_candidates": avoid_candidates,
        "winner_count": len(winners),
        "loser_count": len(losers),
        "memory_ready_for_runtime": bool(items),
        "study_alignment": {
            "attention_engineering": True,
            "episodic_memory": True,
            "mab_ready": True,
        },
    }


def decision_memory_engine_examples() -> dict[str, Any]:
    winner = build_decision_memory_entry(
        axis="hook",
        candidate="se a abertura falha, o resto morre",
        metrics={
            "save_rate": 0.82,
            "share_rate": 0.78,
            "retention": 0.74,
            "replay_proxy": 0.55,
        },
        hypothesis="abertura de confronto aumenta retenção",
        content_type="reel",
        trend="retenção no instagram",
    )
    loser = build_decision_memory_entry(
        axis="format",
        candidate="imagem",
        metrics={
            "save_rate": 0.18,
            "share_rate": 0.09,
            "retention": 0.22,
            "replay_proxy": 0.05,
        },
        hypothesis="imagem simples segura atenção",
        content_type="image",
        trend="clareza e propósito",
    )
    return {
        "ok": True,
        "winner": winner,
        "summary": build_decision_memory_summary(entries=[winner, loser], preferred_axis="hook"),
    }
