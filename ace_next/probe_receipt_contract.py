from __future__ import annotations

from typing import Any

BLOCKED_BRAND = "blocked_brand"
BLOCKED_QUALITY = "blocked_quality"
INTERNAL_LAB = "internal_lab"
EDITORIAL_STAGING = "editorial_staging"
BRAND_LIVE = "brand_live"
TECHNICAL_TEST = "technical_test"

OPERATIONAL_STATES = {
    TECHNICAL_TEST,
    INTERNAL_LAB,
    EDITORIAL_STAGING,
    BRAND_LIVE,
    BLOCKED_BRAND,
    BLOCKED_QUALITY,
}

EVIDENCE_STATES = {
    "no_receipt",
    "receipt_only",
    "receipt_with_media_id",
    "receipt_with_permalink",
    "real_metrics_available",
    "metrics_pending",
    "ingest_error",
}

EVIDENCE_STRENGTHS = {"none", "low", "moderate", "strong"}

RESOLUTION_STATES = {
    "collecting",
    "observe",
    "weak_signal",
    "winner_candidate",
    "loser_candidate",
    "resolved_conservative",
}

RECOMMENDATION_STATES = {
    "collect_more",
    "repeat_probe",
    "wait_metrics",
    "compare_variant",
    "promote_to_editorial_staging_candidate",
    "discard_variant",
    "hold_position",
    "human_review_required",
}

EVIDENCE_BRIDGE_STATES = {
    "no_receipt",
    "probe_requested_without_receipt",
    "receipt_only",
    "receipt_with_media_id",
    "receipt_with_permalink",
    "real_metrics_available",
}

VALID_OPERATIONAL_TRANSITIONS = {
    TECHNICAL_TEST: {INTERNAL_LAB, BLOCKED_QUALITY, BLOCKED_BRAND},
    INTERNAL_LAB: {EDITORIAL_STAGING, BLOCKED_QUALITY, BLOCKED_BRAND},
    EDITORIAL_STAGING: {INTERNAL_LAB, BRAND_LIVE, BLOCKED_QUALITY, BLOCKED_BRAND},
    BRAND_LIVE: {EDITORIAL_STAGING, BLOCKED_QUALITY, BLOCKED_BRAND},
    BLOCKED_QUALITY: {INTERNAL_LAB, EDITORIAL_STAGING},
    BLOCKED_BRAND: {INTERNAL_LAB, EDITORIAL_STAGING},
}

VALID_EVIDENCE_TRANSITIONS = {
    "no_receipt": {"receipt_only", "receipt_with_media_id", "receipt_with_permalink", "real_metrics_available"},
    "receipt_only": {"receipt_with_media_id", "receipt_with_permalink", "real_metrics_available"},
    "receipt_with_media_id": {"receipt_with_permalink", "real_metrics_available"},
    "receipt_with_permalink": {"real_metrics_available"},
    "real_metrics_available": {"real_metrics_available"},
    "metrics_pending": {"receipt_with_media_id", "receipt_with_permalink", "real_metrics_available"},
    "ingest_error": {"metrics_pending", "real_metrics_available"},
}


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _normalize_state(value: Any, allowed: set[str], default: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in allowed:
        return normalized
    return default


def normalize_operational_state(value: Any) -> str:
    return _normalize_state(value, OPERATIONAL_STATES, TECHNICAL_TEST)


def normalize_evidence_state(value: Any) -> str:
    return _normalize_state(value, EVIDENCE_STATES, "no_receipt")


def normalize_evidence_strength(value: Any) -> str:
    return _normalize_state(value, EVIDENCE_STRENGTHS, "none")


def normalize_resolution_state(value: Any) -> str:
    return _normalize_state(value, RESOLUTION_STATES, "collecting")


def normalize_recommendation_state(value: Any) -> str:
    return _normalize_state(value, RECOMMENDATION_STATES, "collect_more")


def is_valid_operational_transition(current_state: Any, next_state: Any) -> bool:
    current = normalize_operational_state(current_state)
    nxt = normalize_operational_state(next_state)
    return nxt == current or nxt in VALID_OPERATIONAL_TRANSITIONS.get(current, set())


def is_valid_evidence_transition(current_state: Any, next_state: Any) -> bool:
    current = normalize_evidence_state(current_state)
    nxt = normalize_evidence_state(next_state)
    return nxt == current or nxt in VALID_EVIDENCE_TRANSITIONS.get(current, set())


def count_real_metrics(real_metrics: dict[str, Any] | None) -> int:
    real_metrics = _safe_dict(real_metrics)
    metric_fields = ("impressions", "reach", "likes", "comments", "saves", "shares")
    return sum(1 for key in metric_fields if real_metrics.get(key) is not None)


def build_probe_payload(probe_context: dict[str, Any] | None) -> dict[str, Any]:
    probe_context = _safe_dict(probe_context)
    return {
        "probe_requested": _normalize_bool(probe_context.get("requested") or probe_context.get("probe_requested")),
        "probe_render_requested": _normalize_bool(
            probe_context.get("render_requested") or probe_context.get("probe_render_requested")
        ),
        "probe_render_executed": _normalize_bool(
            probe_context.get("render_executed") or probe_context.get("probe_render_executed")
        ),
        "probe_publish_executed": _normalize_bool(
            probe_context.get("publish_executed") or probe_context.get("probe_publish_executed")
        ),
        "render_only_mode": _normalize_bool(probe_context.get("render_only_mode")),
        "requested_real_publish": _normalize_bool(
            probe_context.get("allow_real_publish") or probe_context.get("requested_real_publish")
        ),
        "probe_state_requested": probe_context.get("requested_state") or probe_context.get("probe_state_requested"),
        "probe_state_effective": probe_context.get("effective_state") or probe_context.get("probe_state_effective"),
        "probe_block_reason": probe_context.get("probe_block_reason"),
    }


def build_receipt_payload(publish_result: dict[str, Any] | None) -> dict[str, Any]:
    publish_result = _safe_dict(publish_result)
    return {
        "publish_status": publish_result.get("publish_status"),
        "receipt_id": publish_result.get("receipt_id"),
        "media_id": publish_result.get("media_id"),
        "permalink": publish_result.get("permalink"),
        "content_type": publish_result.get("content_type"),
        "style": publish_result.get("style"),
        "created_at": publish_result.get("created_at"),
        "operational_state": publish_result.get("operational_state"),
    }


def derive_evidence_bridge_state(
    *,
    has_receipt: bool,
    has_media_id: bool,
    has_permalink: bool,
    latest_source_status: str | None,
    probe_requested: bool,
) -> str:
    if str(latest_source_status or "") in {"collected", "partial_collected"} and has_media_id:
        return "real_metrics_available"
    if has_receipt and has_media_id and has_permalink:
        return "receipt_with_permalink"
    if has_receipt and has_media_id:
        return "receipt_with_media_id"
    if has_receipt:
        return "receipt_only"
    if probe_requested:
        return "probe_requested_without_receipt"
    return "no_receipt"


def derive_evidence_state(
    *,
    has_receipt: bool,
    has_media_id: bool,
    has_permalink: bool,
    latest_source_status: str | None,
    ingest_attempted: bool,
    metric_count: int,
) -> str:
    source_status = str(latest_source_status or "not_available_yet")
    if source_status == "ingest_error":
        return "ingest_error"
    if source_status in {"collected", "partial_collected"} and has_media_id:
        return "real_metrics_available"
    if not has_receipt:
        return "no_receipt"
    if has_receipt and not has_media_id:
        return "receipt_only"
    if has_receipt and has_media_id and has_permalink:
        return "receipt_with_permalink"
    if has_media_id:
        return "metrics_pending" if ingest_attempted and metric_count == 0 else "receipt_with_media_id"
    return "receipt_only"


def derive_evidence_strength(evidence_state: Any, metric_count: int = 0) -> str:
    normalized = normalize_evidence_state(evidence_state)
    if normalized in {"no_receipt", "ingest_error"}:
        return "none"
    if normalized in {"receipt_only", "metrics_pending"}:
        return "low"
    if normalized == "receipt_with_media_id":
        return "moderate" if metric_count >= 2 else "low"
    if normalized == "receipt_with_permalink":
        return "moderate"
    if normalized == "real_metrics_available":
        return "strong" if metric_count >= 4 else "moderate"
    return "none"


def build_probe_receipt_contract(
    *,
    operational_state: Any,
    publish_result: dict[str, Any] | None = None,
    probe_context: dict[str, Any] | None = None,
    latest_source_status: str | None = None,
    ingest_attempted: bool = False,
    evidence_state: str | None = None,
    evidence_strength: str | None = None,
    resolution_state: str | None = None,
    recommendation_state: str | None = None,
    metric_count: int | None = None,
) -> dict[str, Any]:
    publish_result = _safe_dict(publish_result)
    probe = build_probe_payload(probe_context)
    receipt = build_receipt_payload(publish_result)

    if metric_count is None:
        metric_count = count_real_metrics(_safe_dict(publish_result.get("real_metrics")))

    has_receipt = bool(receipt.get("receipt_id"))
    has_media_id = bool(receipt.get("media_id"))
    has_permalink = bool(receipt.get("permalink"))

    derived_evidence_state = derive_evidence_state(
        has_receipt=has_receipt,
        has_media_id=has_media_id,
        has_permalink=has_permalink,
        latest_source_status=latest_source_status,
        ingest_attempted=bool(ingest_attempted),
        metric_count=metric_count,
    )
    normalized_evidence_state = normalize_evidence_state(evidence_state or derived_evidence_state)
    bridge_state = derive_evidence_bridge_state(
        has_receipt=has_receipt,
        has_media_id=has_media_id,
        has_permalink=has_permalink,
        latest_source_status=latest_source_status,
        probe_requested=probe["probe_requested"],
    )

    return {
        "operational_state": normalize_operational_state(operational_state),
        **probe,
        **receipt,
        "has_real_receipt": has_receipt,
        "has_media_id": has_media_id,
        "has_permalink": has_permalink,
        "latest_source_status": latest_source_status,
        "metric_count": metric_count,
        "evidence_state": normalized_evidence_state,
        "evidence_strength": normalize_evidence_strength(
            evidence_strength or derive_evidence_strength(normalized_evidence_state, metric_count=metric_count)
        ),
        "evidence_bridge_state": bridge_state,
        "resolution_state": normalize_resolution_state(resolution_state),
        "recommendation_state": normalize_recommendation_state(recommendation_state),
    }


def validate_probe_receipt_contract(payload: dict[str, Any] | None) -> dict[str, Any]:
    payload = _safe_dict(payload)
    errors: list[str] = []
    warnings: list[str] = []

    if payload.get("has_permalink") and not payload.get("has_media_id"):
        errors.append("permalink_requires_media_id")
    if payload.get("has_media_id") and not payload.get("has_real_receipt"):
        errors.append("media_id_requires_receipt_id")
    if payload.get("probe_publish_executed") and not payload.get("probe_requested"):
        errors.append("probe_publish_requires_probe_requested")
    if payload.get("probe_render_executed") and not payload.get("probe_render_requested"):
        warnings.append("render_executed_without_render_requested")
    if payload.get("render_only_mode") and payload.get("probe_publish_executed"):
        errors.append("render_only_mode_conflicts_with_probe_publish")
    if payload.get("requested_real_publish") and payload.get("render_only_mode"):
        errors.append("requested_real_publish_conflicts_with_render_only_mode")
    if payload.get("evidence_state") == "no_receipt" and payload.get("has_real_receipt"):
        errors.append("evidence_state_no_receipt_conflicts_with_receipt")
    if payload.get("evidence_state") == "receipt_only" and payload.get("has_media_id"):
        warnings.append("receipt_only_should_upgrade_to_receipt_with_media_id")
    if payload.get("evidence_state") == "receipt_with_media_id" and payload.get("has_permalink"):
        warnings.append("receipt_with_media_id_should_upgrade_to_receipt_with_permalink")
    if payload.get("evidence_state") == "real_metrics_available" and str(payload.get("latest_source_status") or "") not in {
        "collected",
        "partial_collected",
    }:
        warnings.append("real_metrics_available_without_collected_status")
    if payload.get("recommendation_state") == "promote_to_editorial_staging_candidate" and payload.get(
        "operational_state"
    ) == BRAND_LIVE:
        warnings.append("promotion_candidate_on_brand_live_state")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }
