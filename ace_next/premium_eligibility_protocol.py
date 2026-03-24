from __future__ import annotations

from typing import Any


TECHNICAL_TEST = "technical_test"
INTERNAL_LAB = "internal_lab"
EDITORIAL_STAGING = "editorial_staging"
BRAND_LIVE_CANDIDATE = "brand_live_candidate"
BLOCKED_QUALITY = "blocked_quality"
BLOCKED_BRAND = "blocked_brand"

MINIMUMS = {
    "minimum_perceived_value_for_staging": 7.8,
    "minimum_perceived_value_for_brand_live": 8.4,
    "minimum_brand_fit_for_staging": 8.3,
    "minimum_brand_fit_for_brand_live": 8.8,
    "minimum_anti_commodity_for_staging": 8.0,
    "minimum_anti_commodity_for_brand_live": 8.5,
    "minimum_anti_genericity_for_staging": 8.0,
    "minimum_anti_genericity_for_brand_live": 8.4,
    "minimum_naturality_for_staging": 7.8,
    "minimum_naturality_for_brand_live": 8.2,
    "minimum_visual_score_for_staging": 78.0,
    "minimum_visual_score_for_brand_live": 84.0,
    "minimum_rubric_global_for_staging": 8.0,
    "minimum_rubric_global_for_brand_live": 8.8,
}


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return None


def _pick(d: Any, key: str, default: Any = None) -> Any:
    if isinstance(d, dict):
        return d.get(key, default)
    return default


def _first_float(*values: Any) -> float | None:
    for value in values:
        parsed = _safe_float(value)
        if parsed is not None:
            return parsed
    return None


def _infer_editorial_scores(
    creative_plan: dict[str, Any],
    editorial_qa: dict[str, Any],
    rubric_engine: dict[str, Any],
) -> dict[str, float | None]:
    plan = _safe_dict(creative_plan)
    editorial = _safe_dict(_pick(editorial_qa, "breakdown"))
    rubric = _safe_dict(_pick(rubric_engine, "breakdown"))

    headline_len = len(str(_pick(plan, "headline", "") or "").strip())
    hook_len = len(str(_pick(plan, "hook", "") or "").strip())
    clarity_fallback = 8.0 if len(str(_pick(plan, "body", "") or "").strip()) >= 120 else None

    headline_fallback = 7.8 if headline_len >= 24 else 7.2 if headline_len >= 12 else None
    hook_fallback = 7.8 if hook_len >= 40 else 7.2 if hook_len >= 20 else None

    return {
        "perceived_value": _first_float(
            _pick(rubric, "perceived_value"),
            _pick(editorial, "perceived_value"),
        ),
        "anti_commodity": _first_float(
            _pick(rubric, "anti_commodity"),
            _pick(editorial, "anti_commodity"),
        ),
        "anti_genericity": _first_float(
            _pick(rubric, "anti_genericity"),
            _pick(editorial, "anti_genericity"),
            _pick(editorial, "anti_generic"),
        ),
        "naturality": _first_float(
            _pick(rubric, "naturality"),
            _pick(rubric, "naturalism"),
            _pick(editorial, "naturality"),
            _pick(editorial, "naturalism"),
        ),
        "headline": _first_float(
            _pick(rubric, "headline"),
            _pick(editorial, "headline"),
            headline_fallback,
        ),
        "hook": _first_float(
            _pick(rubric, "hook"),
            _pick(editorial, "hook"),
            hook_fallback,
        ),
        "clarity": _first_float(
            _pick(rubric, "clarity"),
            _pick(editorial, "clarity"),
            clarity_fallback,
        ),
    }


def _infer_visual_scores(
    visual_qa: dict[str, Any],
    perceptual_qa: dict[str, Any],
    rubric_engine: dict[str, Any],
) -> dict[str, float | None]:
    visual = _safe_dict(visual_qa)
    perceptual = _safe_dict(perceptual_qa)
    perceptual_breakdown = _safe_dict(_pick(perceptual, "breakdown"))
    rubric = _safe_dict(_pick(rubric_engine, "breakdown"))

    visual_score = _first_float(
        _pick(visual, "final_score"),
        _pick(perceptual, "final_score"),
    )

    return {
        "visual_score": visual_score,
        "composition": _first_float(
            _pick(rubric, "composition"),
            _pick(perceptual_breakdown, "composition"),
        ),
        "contrast": _first_float(
            _pick(rubric, "contrast"),
            _pick(perceptual_breakdown, "contrast"),
        ),
        "legibility": _first_float(
            _pick(rubric, "legibility"),
            _pick(perceptual_breakdown, "legibility"),
        ),
    }


def _infer_brand_scores(
    rubric_engine: dict[str, Any],
    brand_veto_gate: dict[str, Any],
) -> dict[str, Any]:
    rubric = _safe_dict(rubric_engine)
    rubric_breakdown = _safe_dict(_pick(rubric, "breakdown"))
    brand_veto = _safe_dict(brand_veto_gate)

    return {
        "brand_fit": _first_float(_pick(rubric_breakdown, "brand_fit")),
        "global_score": _first_float(_pick(rubric, "global_score")),
        "global_score_100": _first_float(_pick(rubric, "global_score_100")),
        "brand_veto_approved": _safe_bool(_pick(brand_veto, "approved")),
        "brand_veto_blocked": _safe_bool(_pick(brand_veto, "blocked")),
    }


def _infer_authorization_state(publication_authorization_gate: dict[str, Any]) -> dict[str, Any]:
    gate = _safe_dict(publication_authorization_gate)
    return {
        "selected_state": _pick(gate, "selected_state"),
        "requires_human_review": _safe_bool(_pick(gate, "requires_human_review")),
        "can_publish_real": _safe_bool(_pick(gate, "can_publish_real")),
        "main_surface_allowed": _safe_bool(_pick(gate, "main_surface_allowed")),
    }


def _mean(values: list[float | None]) -> float:
    valid = [float(v) for v in values if v is not None]
    if not valid:
        return 0.0
    return round(sum(valid) / len(valid), 2)


def _is_severe_failure(field: str, value: float | None) -> bool:
    if value is None:
        return field in {
            "perceived_value",
            "brand_fit",
            "anti_commodity",
            "anti_genericity",
            "naturality",
            "visual_score",
            "global_score",
        }

    if field == "visual_score":
        return value < (MINIMUMS["minimum_visual_score_for_staging"] - 10.0)

    if field == "global_score":
        return value < (MINIMUMS["minimum_rubric_global_for_staging"] - 0.8)

    return value < (MINIMUMS[f"minimum_{field}_for_staging"] - 0.8)


def evaluate_premium_eligibility_protocol(
    *,
    creative_plan: dict | None = None,
    editorial_qa: dict | None = None,
    visual_qa: dict | None = None,
    perceptual_qa: dict | None = None,
    rubric_engine: dict | None = None,
    brand_veto_gate: dict | None = None,
    publication_authorization_gate: dict | None = None,
) -> dict:
    creative_plan = _safe_dict(creative_plan)
    editorial_qa = _safe_dict(editorial_qa)
    visual_qa = _safe_dict(visual_qa)
    perceptual_qa = _safe_dict(perceptual_qa)
    rubric_engine = _safe_dict(rubric_engine)
    brand_veto_gate = _safe_dict(brand_veto_gate)
    publication_authorization_gate = _safe_dict(publication_authorization_gate)

    editorial_scores = _infer_editorial_scores(creative_plan, editorial_qa, rubric_engine)
    visual_scores = _infer_visual_scores(visual_qa, perceptual_qa, rubric_engine)
    brand_scores = _infer_brand_scores(rubric_engine, brand_veto_gate)
    authorization_state = _infer_authorization_state(publication_authorization_gate)

    observed_scores = {
        "perceived_value": editorial_scores["perceived_value"],
        "brand_fit": brand_scores["brand_fit"],
        "anti_commodity": editorial_scores["anti_commodity"],
        "anti_genericity": editorial_scores["anti_genericity"],
        "naturality": editorial_scores["naturality"],
        "headline": editorial_scores["headline"],
        "hook": editorial_scores["hook"],
        "clarity": editorial_scores["clarity"],
        "composition": visual_scores["composition"],
        "contrast": visual_scores["contrast"],
        "legibility": visual_scores["legibility"],
        "visual_score": visual_scores["visual_score"],
        "global_score": brand_scores["global_score"],
        "global_score_100": brand_scores["global_score_100"],
        "selected_state": authorization_state["selected_state"],
        "brand_veto_approved": brand_scores["brand_veto_approved"],
        "brand_veto_blocked": brand_scores["brand_veto_blocked"],
    }

    failed_checks: list[str] = []
    reasons: list[str] = []

    brand_blocked = bool(brand_scores["brand_veto_blocked"])
    if brand_blocked:
        failed_checks.append("brand_veto_blocked")
        reasons.append("peça bloqueada por risco de marca")

    staging_checks = {
        "perceived_value": editorial_scores["perceived_value"],
        "brand_fit": brand_scores["brand_fit"],
        "anti_commodity": editorial_scores["anti_commodity"],
        "anti_genericity": editorial_scores["anti_genericity"],
        "naturality": editorial_scores["naturality"],
        "visual_score": visual_scores["visual_score"],
        "global_score": brand_scores["global_score"],
    }

    severe_quality_fail = False
    passed_staging = True
    passed_brand_live = True

    for field, value in staging_checks.items():
        staging_key = f"minimum_{field}_for_staging"
        brand_key = f"minimum_{field}_for_brand_live"

        if value is None:
            failed_checks.append(f"missing_{field}")
            reasons.append(f"dado ausente para {field}")
            passed_staging = False
            passed_brand_live = False
            if _is_severe_failure(field, value):
                severe_quality_fail = True
            continue

        staging_minimum = MINIMUMS[staging_key]
        brand_minimum = MINIMUMS[brand_key]

        if float(value) < staging_minimum:
            failed_checks.append(f"below_staging_{field}")
            reasons.append(f"{field} abaixo do mínimo de staging")
            passed_staging = False
            if _is_severe_failure(field, value):
                severe_quality_fail = True

        if float(value) < brand_minimum:
            failed_checks.append(f"below_brand_live_{field}")
            passed_brand_live = False

    editorial_approved = _safe_bool(_pick(editorial_qa, "approved"))
    visual_approved = _safe_bool(_pick(visual_qa, "approved"))
    perceptual_approved = _safe_bool(_pick(perceptual_qa, "approved"))
    rubric_minimum_quality = _safe_bool(_pick(rubric_engine, "approved_minimum_quality"))

    if editorial_approved is False:
        failed_checks.append("editorial_qa_not_approved")
        reasons.append("editorial_qa não aprovado")
        severe_quality_fail = True
    if visual_approved is False:
        failed_checks.append("visual_qa_not_approved")
        reasons.append("visual_qa não aprovado")
        severe_quality_fail = True
    if perceptual_approved is False:
        failed_checks.append("perceptual_qa_not_approved")
        reasons.append("perceptual_qa não aprovado")
        severe_quality_fail = True
    if rubric_minimum_quality is False:
        failed_checks.append("rubric_minimum_quality_not_approved")
        reasons.append("rubric global abaixo do piso mínimo soberano")
        severe_quality_fail = True

    premium_score = _mean(
        [
            editorial_scores["perceived_value"],
            brand_scores["brand_fit"],
            editorial_scores["anti_commodity"],
            editorial_scores["anti_genericity"],
            editorial_scores["naturality"],
            editorial_scores["headline"],
            editorial_scores["hook"],
            editorial_scores["clarity"],
            visual_scores["composition"],
            visual_scores["contrast"],
            visual_scores["legibility"],
            brand_scores["global_score"],
        ]
    )

    current_state = str(authorization_state["selected_state"] or "").strip()

    if brand_blocked:
        classification = BLOCKED_BRAND
    elif severe_quality_fail:
        classification = BLOCKED_QUALITY
    elif passed_brand_live:
        classification = BRAND_LIVE_CANDIDATE
    elif passed_staging:
        classification = EDITORIAL_STAGING
    elif current_state == TECHNICAL_TEST:
        classification = TECHNICAL_TEST
    else:
        classification = INTERNAL_LAB

    eligible_for_lab = classification in {
        TECHNICAL_TEST,
        INTERNAL_LAB,
        EDITORIAL_STAGING,
        BRAND_LIVE_CANDIDATE,
    }
    eligible_for_editorial_staging = classification in {
        EDITORIAL_STAGING,
        BRAND_LIVE_CANDIDATE,
    }
    eligible_for_brand_live_candidate = classification == BRAND_LIVE_CANDIDATE
    blocked_by_quality = classification == BLOCKED_QUALITY
    blocked_by_brand = classification == BLOCKED_BRAND
    requires_human_review = True
    brand_live_allowed_now = False

    if classification == BLOCKED_BRAND:
        next_best_state = BLOCKED_BRAND
        summary = "peça bloqueada por risco de marca"
    elif classification == BLOCKED_QUALITY:
        next_best_state = INTERNAL_LAB
        summary = "peça bloqueada por qualidade premium insuficiente"
    elif classification == TECHNICAL_TEST:
        next_best_state = INTERNAL_LAB
        summary = "peça restrita a teste técnico"
    elif classification == INTERNAL_LAB:
        next_best_state = EDITORIAL_STAGING
        summary = "peça autorizada apenas para laboratório interno"
    elif classification == EDITORIAL_STAGING:
        next_best_state = BRAND_LIVE_CANDIDATE
        summary = "peça aprovada apenas para editorial_staging"
    else:
        next_best_state = BRAND_LIVE_CANDIDATE
        summary = "peça candidata a brand_live, mas ainda sob revisão humana obrigatória"

    if not reasons:
        reasons.append(summary)

    return {
        "ok": True,
        "classification": classification,
        "eligible_for_lab": eligible_for_lab,
        "eligible_for_editorial_staging": eligible_for_editorial_staging,
        "eligible_for_brand_live_candidate": eligible_for_brand_live_candidate,
        "blocked_by_quality": blocked_by_quality,
        "blocked_by_brand": blocked_by_brand,
        "requires_human_review": requires_human_review,
        "brand_live_allowed_now": brand_live_allowed_now,
        "premium_score": premium_score,
        "minimums": dict(MINIMUMS),
        "observed_scores": observed_scores,
        "failed_checks": failed_checks,
        "reasons": reasons,
        "next_best_state": next_best_state,
        "summary": summary,
    }


def premium_eligibility_protocol_examples() -> dict:
    lab_example = evaluate_premium_eligibility_protocol(
        editorial_qa={"approved": True, "breakdown": {"perceived_value": 7.4, "anti_commodity": 7.7, "anti_genericity": 7.7, "naturalism": 7.6, "headline": 7.9, "hook": 7.8, "clarity": 8.0}},
        visual_qa={"approved": True, "final_score": 76},
        perceptual_qa={"approved": True, "breakdown": {"composition": 7.6, "contrast": 7.8, "legibility": 7.9}},
        rubric_engine={"approved_minimum_quality": True, "global_score": 7.9, "global_score_100": 79, "breakdown": {"brand_fit": 8.1}},
        brand_veto_gate={"approved": True, "blocked": False},
        publication_authorization_gate={"selected_state": "internal_lab"},
    )

    staging_example = evaluate_premium_eligibility_protocol(
        editorial_qa={"approved": True, "breakdown": {"perceived_value": 8.0, "anti_commodity": 8.2, "anti_genericity": 8.1, "naturalism": 8.0, "headline": 8.0, "hook": 8.1, "clarity": 8.2}},
        visual_qa={"approved": True, "final_score": 80},
        perceptual_qa={"approved": True, "breakdown": {"composition": 8.0, "contrast": 8.2, "legibility": 8.4}},
        rubric_engine={"approved_minimum_quality": True, "global_score": 8.2, "global_score_100": 82, "breakdown": {"brand_fit": 8.5}},
        brand_veto_gate={"approved": True, "blocked": False},
        publication_authorization_gate={"selected_state": "editorial_staging"},
    )

    brand_live_example = evaluate_premium_eligibility_protocol(
        editorial_qa={"approved": True, "breakdown": {"perceived_value": 8.7, "anti_commodity": 8.7, "anti_genericity": 8.5, "naturalism": 8.4, "headline": 8.5, "hook": 8.6, "clarity": 8.6}},
        visual_qa={"approved": True, "final_score": 86},
        perceptual_qa={"approved": True, "breakdown": {"composition": 8.6, "contrast": 8.6, "legibility": 8.7}},
        rubric_engine={"approved_minimum_quality": True, "global_score": 8.9, "global_score_100": 89, "breakdown": {"brand_fit": 8.9}},
        brand_veto_gate={"approved": True, "blocked": False},
        publication_authorization_gate={"selected_state": "editorial_staging"},
    )

    return {
        "ok": True,
        "lab_example": lab_example,
        "staging_example": staging_example,
        "brand_live_candidate_example": brand_live_example,
    }
