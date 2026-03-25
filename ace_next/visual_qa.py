from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .brand_dignity_score import evaluate_brand_dignity_score
from .visual_hierarchy_gate import evaluate_visual_hierarchy_gate
from .visual_templates_premium import resolve_premium_visual_template


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            return {}
    return {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _line_estimate(text: str, chars_per_line: int) -> int:
    text = _clean_text(text)
    if not text:
        return 0
    return max(1, (len(text) + max(1, chars_per_line) - 1) // max(1, chars_per_line))


def _build_gate_contract(plan: dict[str, Any], template_meta: dict[str, Any]) -> dict[str, Any]:
    headline = _clean_text(plan.get("headline"))
    hook = _clean_text(plan.get("hook"))
    body = _clean_text(plan.get("body"))
    cta = _clean_text(plan.get("cta"))
    support_points = plan.get("support_points")
    if not isinstance(support_points, list):
        support_points = []
    support_points = [_clean_text(x) for x in support_points if _clean_text(x)]

    return {
        "brand_system": {
            "text_contrast_policy": "premium_high_contrast",
            "brand_dignity_constraints": {
                "anti_generic_identity_rules": [
                    "evitar template barato",
                    "evitar copy commodity",
                    "evitar excesso visual",
                ]
            },
        },
        "template_spec": template_meta,
        "layout_payload": {
            "display_payload": {
                "headline": headline,
                "hook": hook,
                "body": body,
                "cta": cta,
                "support_points": support_points,
            }
        },
        "gate_payload": {
            "computed_line_estimates": {
                "headline_lines": _line_estimate(headline, 28),
                "hook_lines": _line_estimate(hook, 36),
                "body_lines": _line_estimate(body, 46),
                "cta_lines": _line_estimate(cta, 34),
            },
            "line_expectations": {
                "headline_lines": 3,
                "hook_lines": 2,
                "body_lines": 4,
                "cta_lines": 2,
            },
            "minimum_scores": {
                "brand_dignity_score": 7.8,
                "contrast_score": 7.0,
                "composition_score": 7.4,
                "legibility_score": 7.5,
                "hierarchy_score": 7.5,
                "noise_control_score": 7.2,
            },
        },
    }


def _base_visual_score(plan: dict[str, Any], identity: dict[str, Any], typography: dict[str, Any], template_meta: dict[str, Any]) -> float:
    score = 74.0
    if identity:
        score += 4.0
    if typography:
        score += 4.0
    if template_meta.get("premium_tier"):
        score += 4.0

    headline = _clean_text(plan.get("headline"))
    hook = _clean_text(plan.get("hook"))
    body = _clean_text(plan.get("body"))
    cta = _clean_text(plan.get("cta"))
    support_points = plan.get("support_points")
    if not isinstance(support_points, list):
        support_points = []

    if 18 <= len(headline) <= 92:
        score += 3.0
    if 18 <= len(hook) <= 120:
        score += 2.0
    if len(body) <= 280:
        score += 2.0
    if len(cta) <= 72:
        score += 1.5
    if len(support_points) <= 3:
        score += 1.5

    return round(min(score, 92.0), 2)


@dataclass
class VisualQualityResult:
    approved: bool
    final_score: float
    minimum_score: int
    breakdown: dict[str, Any]
    metrics: dict[str, Any]
    reasons: list[str]
    recommendations: list[str]
    hierarchy_gate: dict[str, Any]
    brand_dignity_score: dict[str, Any]
    premium_template_hint: dict[str, Any]
    failed_floors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_visual_quality(
    plan: dict,
    identity,
    typography,
):
    plan = _safe_dict(plan)
    identity_dict = _safe_dict(identity)
    typography_dict = _safe_dict(typography)

    template_meta = resolve_premium_visual_template(
        use_case="contrast" if "erro" in _clean_text(plan.get("angle")).lower() else None,
        strategic_format=plan.get("strategic_target_format") or plan.get("publish_format_now"),
    )

    gate_contract = _build_gate_contract(plan, template_meta)

    reasons: list[str] = []
    recommendations: list[str] = []
    failed_floors: list[str] = []

    base_score = _base_visual_score(plan, identity_dict, typography_dict, template_meta)

    try:
        hierarchy_gate = evaluate_visual_hierarchy_gate(gate_contract)
    except Exception as exc:
        hierarchy_gate = {
            "ok": False,
            "approved": False,
            "final_score": base_score,
            "breakdown": {},
            "failed_floors": ["hierarchy_gate_runtime_error"],
            "rejection_reasons": [f"hierarchy gate falhou: {type(exc).__name__}: {exc}"],
            "recommendations": ["revisar gate de hierarquia"],
            "metrics": {},
        }
        reasons.append(f"hierarchy_gate_error: {type(exc).__name__}: {exc}")

    try:
        dignity_score = evaluate_brand_dignity_score(
            creative_plan=plan,
            visual_qa={"final_score": base_score},
            hierarchy_gate=hierarchy_gate,
            template_meta=template_meta,
        )
    except Exception as exc:
        dignity_score = {
            "ok": False,
            "approved": False,
            "final_score": round(base_score / 10.0, 2),
            "classification": "borderline",
            "breakdown": {},
            "failed_floors": ["brand_dignity_runtime_error"],
            "reasons": [f"brand dignity falhou: {type(exc).__name__}: {exc}"],
            "recommendations": ["revisar dignity score"],
            "signals": {},
        }
        reasons.append(f"brand_dignity_error: {type(exc).__name__}: {exc}")

    hierarchy_final = float(hierarchy_gate.get("final_score") or base_score)
    dignity_final = float(dignity_score.get("final_score") or (base_score / 10.0))

    final_score = round((base_score * 0.50) + (hierarchy_final * 0.25) + ((dignity_final * 10.0) * 0.25), 2)

    breakdown = {
        "visual_score_base": round(base_score, 2),
        "hierarchy_gate_score": round(hierarchy_final, 2),
        "brand_dignity_score": round(dignity_final * 10.0, 2),
    }

    metrics = {
        "headline_chars": len(_clean_text(plan.get("headline"))),
        "hook_chars": len(_clean_text(plan.get("hook"))),
        "body_chars": len(_clean_text(plan.get("body"))),
        "cta_chars": len(_clean_text(plan.get("cta"))),
        "support_points_count": len(plan.get("support_points") or []),
        "template_id": template_meta.get("template_id"),
    }

    reasons.extend(hierarchy_gate.get("rejection_reasons") or [])
    reasons.extend(dignity_score.get("reasons") or [])
    recommendations.extend(hierarchy_gate.get("recommendations") or [])
    recommendations.extend(dignity_score.get("recommendations") or [])
    failed_floors.extend(hierarchy_gate.get("failed_floors") or [])
    failed_floors.extend(dignity_score.get("failed_floors") or [])

    approved = (
        final_score >= 78
        and bool(hierarchy_gate.get("approved"))
        and dignity_score.get("classification") != "brand_indignity"
    )

    if not approved and final_score < 78:
        failed_floors.append("final_score_below_minimum")
    if dignity_score.get("classification") == "brand_indignity":
        failed_floors.append("brand_indignity")
    if not hierarchy_gate.get("approved"):
        failed_floors.append("hierarchy_gate_not_approved")

    dedup_failed = []
    for item in failed_floors:
        if item not in dedup_failed:
            dedup_failed.append(item)

    dedup_reasons = []
    for item in reasons:
        if item not in dedup_reasons:
            dedup_reasons.append(item)

    dedup_recommendations = []
    for item in recommendations:
        if item not in dedup_recommendations:
            dedup_recommendations.append(item)

    return VisualQualityResult(
        approved=approved,
        final_score=final_score,
        minimum_score=78,
        breakdown=breakdown,
        metrics=metrics,
        reasons=dedup_reasons,
        recommendations=dedup_recommendations,
        hierarchy_gate=hierarchy_gate,
        brand_dignity_score=dignity_score,
        premium_template_hint=template_meta,
        failed_floors=dedup_failed,
    )
