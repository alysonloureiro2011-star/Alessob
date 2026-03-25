from __future__ import annotations

from typing import Any

CONTINUITY_NONE = "no_continuity"
CONTINUITY_HYPOTHESIS = "continuity_hypothesis"
CONTINUITY_CONFIRMED = "continuity_confirmed"

CONTINUITY_STATES = {
    CONTINUITY_NONE,
    CONTINUITY_HYPOTHESIS,
    CONTINUITY_CONFIRMED,
}


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_continuity_state(value: Any) -> str:
    normalized = _clean(value).lower()
    if normalized in CONTINUITY_STATES:
        return normalized
    return CONTINUITY_NONE


def classify_continuity(serial_continuity: dict[str, Any] | None) -> dict[str, Any]:
    serial = _safe_dict(serial_continuity)

    recent_match_found = bool(
        serial.get("recent_match_found")
        or serial.get("matched_episode_id")
        or serial.get("previous_episode_id")
    )
    keyword_overlap = _safe_int(
        _safe_dict(serial.get("continuity_signals")).get("keyword_overlap")
        or serial.get("keyword_overlap")
        or 0
    )
    sequel_candidate = bool(
        serial.get("sequel_candidate")
        or serial.get("linked_series_candidate")
    )
    source_mode = _clean(serial.get("source_mode") or serial.get("continuity_source_mode") or "conservative_fallback")
    continuity_confidence = _clean(serial.get("continuity_confidence") or "low")

    if recent_match_found and keyword_overlap >= 2:
        continuity_state = CONTINUITY_CONFIRMED
        continuity_reason = _clean(
            serial.get("continuity_reason")
            or "há continuidade real suficiente com episódio anterior"
        )
    elif sequel_candidate:
        continuity_state = CONTINUITY_HYPOTHESIS
        continuity_reason = _clean(
            serial.get("continuity_reason")
            or "há apenas hipótese conservadora de continuidade"
        )
    else:
        continuity_state = CONTINUITY_NONE
        continuity_reason = _clean(
            serial.get("continuity_reason")
            or "não existe continuidade suficiente confirmada"
        )

    return {
        "continuity_state": continuity_state,
        "continuity_reason": continuity_reason,
        "continuity_confidence": continuity_confidence,
        "continuity_source_mode": source_mode,
        "linked_series_candidate": continuity_state in {CONTINUITY_CONFIRMED, CONTINUITY_HYPOTHESIS},
        "sequel_candidate": sequel_candidate,
    }


def build_episode_lineage(record: dict[str, Any] | None, serial_continuity: dict[str, Any] | None) -> dict[str, Any]:
    record = _safe_dict(record)
    serial = _safe_dict(serial_continuity)
    continuity = classify_continuity(serial)

    matched_episode_id = _clean(
        serial.get("matched_episode_id")
        or serial.get("previous_episode_id")
        or serial.get("recent_episode_id")
        or serial.get("candidate_episode_id")
    ) or None

    previous_episode_id = matched_episode_id if continuity["continuity_state"] == CONTINUITY_CONFIRMED else None
    parent_episode_id = _clean(
        serial.get("parent_episode_id")
        or previous_episode_id
        or matched_episode_id
    ) or None

    episode_index_hint = _safe_int(serial.get("episode_index_hint") or 1, 1)
    if episode_index_hint <= 0:
        episode_index_hint = 1

    return {
        "episode_id": _clean(record.get("record_id") or record.get("episode_id")) or None,
        "series_name": _clean(
            serial.get("series_name")
            or _safe_dict(record.get("creative_plan")).get("series_name")
            or "Liberta a Verdade"
        ),
        "episode_index_hint": episode_index_hint,
        "previous_episode_id": previous_episode_id,
        "parent_episode_id": parent_episode_id,
        "linked_series_candidate": continuity["linked_series_candidate"],
        "sequel_candidate": continuity["sequel_candidate"],
        "next_episode_seed": _clean(serial.get("next_episode_seed")) or None,
        "carryover_problem": _clean(serial.get("carryover_problem")) or None,
        "carryover_hook": _clean(serial.get("carryover_hook")) or None,
        "carryover_payoff": _clean(serial.get("carryover_payoff")) or None,
        "continuity_state": continuity["continuity_state"],
        "continuity_confidence": continuity["continuity_confidence"],
        "continuity_reason": continuity["continuity_reason"],
        "continuity_source_mode": continuity["continuity_source_mode"],
    }


def build_episode_memory_contract(
    *,
    record: dict[str, Any] | None,
    serial_continuity: dict[str, Any] | None,
) -> dict[str, Any]:
    record = _safe_dict(record)
    creative_plan = _safe_dict(record.get("creative_plan"))
    lineage = build_episode_lineage(record, serial_continuity)

    return {
        **lineage,
        "topic_seed": _clean(creative_plan.get("topic_seed") or creative_plan.get("trend_input")),
        "continuity_real": lineage["continuity_state"] == CONTINUITY_CONFIRMED,
        "continuity_hypothesis_only": lineage["continuity_state"] == CONTINUITY_HYPOTHESIS,
        "continuity_absent": lineage["continuity_state"] == CONTINUITY_NONE,
    }
