from __future__ import annotations

from typing import Any

TECHNICAL_TEST = "technical_test"
INTERNAL_LAB = "internal_lab"
EDITORIAL_STAGING = "editorial_staging"
BRAND_LIVE_CANDIDATE = "brand_live_candidate"
BRAND_LIVE = "brand_live"
BLOCKED_QUALITY = "blocked_quality"
BLOCKED_BRAND = "blocked_brand"

STAGING_FLOORS = {
    "perceived_value": 7.8,
    "brand_fit": 8.3,
    "anti_commodity": 8.0,
    "anti_genericity": 8.0,
    "global_score": 8.0,
    "hierarchy": 7.8,
    "clarity": 7.8,
}

BRAND_LIVE_FLOORS = {
    "perceived_value": 8.4,
    "brand_fit": 8.8,
    "anti_commodity": 8.5,
    "anti_genericity": 8.4,
    "global_score": 8.8,
    "hierarchy": 8.4,
    "clarity": 8.4,
}

VETO_FLOORS = {
    "headline": 7.5,
    "hook": 7.5,
    "naturalism": 7.8,
    "legibility": 7.0,
    "contrast": 7.0,
    "composition": 7.0,
}


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _round(value: float | None) -> float | None:
    if value is None:
        return None
    return round(float(value), 2)


def _gap(current: float | None, target: float) -> float:
    if current is None:
        return round(target, 2)
    return round(max(0.0, target - float(current)), 2)


def build_observed_scores(
    *,
    rubric_breakdown: dict[str, Any],
    global_score: Any,
    post_hardening_scores: dict[str, Any] | None = None,
) -> dict[str, float | None]:
    rubric_breakdown = _safe_dict(rubric_breakdown)
    post_hardening_scores = _safe_dict(post_hardening_scores)

    hierarchy_score = (
        _safe_float(post_hardening_scores.get("hierarchy_score"))
        or _safe_float(post_hardening_scores.get("hierarchy_final_score"))
        or _safe_float(rubric_breakdown.get("hierarchy"))
        or _safe_float(rubric_breakdown.get("composition"))
    )

    return {
        "perceived_value": _safe_float(rubric_breakdown.get("perceived_value")),
        "brand_fit": _safe_float(rubric_breakdown.get("brand_fit")),
        "anti_commodity": _safe_float(rubric_breakdown.get("anti_commodity")),
        "anti_genericity": _safe_float(rubric_breakdown.get("anti_genericity")),
        "global_score": _safe_float(global_score),
        "hierarchy": hierarchy_score,
        "clarity": _safe_float(rubric_breakdown.get("clarity")),
        "headline": _safe_float(rubric_breakdown.get("headline")),
        "hook": _safe_float(rubric_breakdown.get("hook")),
        "naturalism": _safe_float(rubric_breakdown.get("naturalism")),
        "legibility": _safe_float(rubric_breakdown.get("legibility")),
        "contrast": _safe_float(rubric_breakdown.get("contrast")),
        "composition": _safe_float(rubric_breakdown.get("composition")),
    }


def evaluate_floors(
    observed_scores: dict[str, float | None],
    floors: dict[str, float],
) -> dict[str, Any]:
    details: dict[str, Any] = {}
    failed: list[str] = []

    for key, required in floors.items():
        observed = _safe_float(observed_scores.get(key))
        passed = observed is not None and observed >= required
        details[key] = {
            "observed": _round(observed),
            "required": _round(required),
            "gap": _gap(observed, required),
            "passed": passed,
        }
        if not passed:
            failed.append(key)

    return {
        "passed": not failed,
        "failed": failed,
        "details": details,
    }


def build_delta_to_brand_live(observed_scores: dict[str, float | None]) -> dict[str, Any]:
    brand_live_eval = evaluate_floors(observed_scores, BRAND_LIVE_FLOORS)
    details = brand_live_eval["details"]

    missing_for_brand_live = [key for key in brand_live_eval["failed"]]
    targets = sorted(
        [
            {
                "metric": key,
                "current": details[key]["observed"],
                "target": details[key]["required"],
                "gap": details[key]["gap"],
            }
            for key in missing_for_brand_live
        ],
        key=lambda item: item["gap"],
        reverse=True,
    )

    score_gap_to_brand_live = _round(max([item["gap"] for item in targets], default=0.0))
    next_quality_lift_targets = targets[:4]

    return {
        "missing_for_brand_live": missing_for_brand_live,
        "score_gap_to_brand_live": score_gap_to_brand_live,
        "next_quality_lift_targets": next_quality_lift_targets,
        "brand_live_floor_details": details,
    }


def build_promotion_readiness_summary(
    *,
    observed_scores: dict[str, float | None],
    brand_veto_blocked: bool,
    current_classification: str,
) -> dict[str, Any]:
    staging_eval = evaluate_floors(observed_scores, STAGING_FLOORS)
    brand_live_eval = evaluate_floors(observed_scores, BRAND_LIVE_FLOORS)
    veto_eval = evaluate_floors(observed_scores, VETO_FLOORS)
    delta = build_delta_to_brand_live(observed_scores)

    if brand_veto_blocked:
        readiness = "blocked_brand"
    elif not staging_eval["passed"]:
        readiness = "blocked_quality"
    elif brand_live_eval["passed"] and veto_eval["passed"]:
        readiness = "brand_live_candidate"
    else:
        readiness = "editorial_staging"

    return {
        "current_classification": current_classification,
        "readiness": readiness,
        "staging_floor_passed": staging_eval["passed"],
        "brand_live_floor_passed": brand_live_eval["passed"],
        "veto_floor_passed": veto_eval["passed"],
        "failed_staging_floors": staging_eval["failed"],
        "failed_brand_live_floors": brand_live_eval["failed"],
        "failed_veto_floors": veto_eval["failed"],
        **delta,
    }


def _is_severe_quality_failure(observed_scores: dict[str, float | None]) -> bool:
    severe_keys = ("perceived_value", "brand_fit", "anti_commodity", "global_score", "hierarchy", "clarity")
    for key in severe_keys:
        current = _safe_float(observed_scores.get(key))
        target = STAGING_FLOORS[key]
        if current is None or (target - current) >= 0.8:
            return True
    return False


def decide_publication_state(
    *,
    force_placeholder: bool,
    observed_scores: dict[str, float | None],
    brand_veto_blocked: bool,
    require_human_review: bool = True,
) -> dict[str, Any]:
    staging_eval = evaluate_floors(observed_scores, STAGING_FLOORS)
    brand_live_eval = evaluate_floors(observed_scores, BRAND_LIVE_FLOORS)
    veto_eval = evaluate_floors(observed_scores, VETO_FLOORS)
    delta = build_delta_to_brand_live(observed_scores)

    reasons: list[str] = []

    if force_placeholder:
        classification = TECHNICAL_TEST
        selected_state = TECHNICAL_TEST
        reasons.append("placeholder técnico solicitado")
    elif brand_veto_blocked:
        classification = BLOCKED_BRAND
        selected_state = BLOCKED_BRAND
        reasons.append("brand_veto bloqueou a peça")
    elif not staging_eval["passed"]:
        classification = BLOCKED_QUALITY if _is_severe_quality_failure(observed_scores) else INTERNAL_LAB
        selected_state = classification
        reasons.append("pisos de staging ainda insuficientes")
    elif brand_live_eval["passed"] and veto_eval["passed"]:
        classification = BRAND_LIVE_CANDIDATE if require_human_review else BRAND_LIVE
        selected_state = EDITORIAL_STAGING if classification == BRAND_LIVE_CANDIDATE else BRAND_LIVE
        reasons.append("pisos de brand_live atingidos, mas a promoção ainda depende de revisão humana")
    else:
        classification = EDITORIAL_STAGING
        selected_state = EDITORIAL_STAGING
        reasons.append("peça aprovada para staging, mas ainda abaixo do piso de brand_live")

    summary = {
        TECHNICAL_TEST: "restrito a teste técnico",
        INTERNAL_LAB: "autorizado apenas para laboratório interno",
        EDITORIAL_STAGING: "autorizado para editorial_staging",
        BRAND_LIVE_CANDIDATE: "candidato a brand_live, ainda sem promoção automática",
        BRAND_LIVE: "elegível a brand_live sob revisão humana explícita",
        BLOCKED_QUALITY: "bloqueado por qualidade",
        BLOCKED_BRAND: "bloqueado por marca",
    }[classification]

    return {
        "classification": classification,
        "selected_state": selected_state,
        "summary": summary,
        "reasons": reasons,
        "requires_human_review": require_human_review,
        "eligible_for_editorial_staging": classification in {EDITORIAL_STAGING, BRAND_LIVE_CANDIDATE, BRAND_LIVE},
        "eligible_for_brand_live_candidate": classification in {BRAND_LIVE_CANDIDATE, BRAND_LIVE},
        "brand_live_candidate": classification == BRAND_LIVE_CANDIDATE,
        "brand_live_allowed_now": classification == BRAND_LIVE and not require_human_review,
        "failed_staging_floors": staging_eval["failed"],
        "failed_brand_live_floors": brand_live_eval["failed"],
        "failed_veto_floors": veto_eval["failed"],
        **delta,
    }


def build_payload_comparison(
    *,
    raw_payload: dict[str, Any] | None,
    rewritten_payload: dict[str, Any] | None,
    authorized_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    raw_payload = _safe_dict(raw_payload)
    rewritten_payload = _safe_dict(rewritten_payload)
    authorized_payload = _safe_dict(authorized_payload)

    keys = ("problem", "payoff", "cta", "headline", "hook", "body")
    changes: list[dict[str, Any]] = []

    for key in keys:
        raw_value = raw_payload.get(key)
        rewritten_value = rewritten_payload.get(key)
        authorized_value = authorized_payload.get(key)

        if raw_value != rewritten_value or rewritten_value != authorized_value:
            changes.append(
                {
                    "field": key,
                    "raw": raw_value,
                    "rewritten": rewritten_value,
                    "authorized": authorized_value,
                }
            )

    return {
        "changed_fields": changes,
        "changed_fields_count": len(changes),
        "raw_present": bool(raw_payload),
        "rewritten_present": bool(rewritten_payload),
        "authorized_present": bool(authorized_payload),
    }
