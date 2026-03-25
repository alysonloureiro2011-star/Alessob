from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .perceived_value_rewriter import build_perceived_value_rewriter
from .rubric_engine import RubricEngineResult


@dataclass
class BrandVetoResult:
    approved: bool
    blocked: bool
    categories: dict[str, bool]
    triggers: list[str]
    reasons: list[str]
    summary: str
    evaluation_payload_source: str | None
    hardening_considered: bool
    post_hardening_brand_veto: dict[str, Any]
    pre_rewrite_state: str | None
    post_rewrite_state: str | None
    raw_payload_vs_rewritten_payload: dict[str, Any]
    rewritten_payload_vs_authorized_payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            return {}
    return {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _resolve_authority_payload(
    plan: dict[str, Any],
    visual_qa: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], str]:
    plan = _safe_dict(plan)
    visual_qa = _safe_dict(visual_qa)
    metrics = _safe_dict(visual_qa.get("metrics"))

    if _safe_dict(plan.get("authority_payload")):
        rewrite = {
            "authority_payload": _safe_dict(plan.get("authority_payload")),
            "pre_rewrite_state": plan.get("pre_rewrite_state"),
            "post_rewrite_state": plan.get("post_rewrite_state"),
            "raw_payload_vs_rewritten_payload": _safe_dict(plan.get("raw_payload_vs_rewritten_payload")),
        }
        return _safe_dict(plan.get("authority_payload")), rewrite, "creative_plan.authority_payload"

    render_payload_used = _safe_dict(metrics.get("render_payload_used"))
    if render_payload_used:
        rewrite = build_perceived_value_rewriter(render_payload_used)
        return _safe_dict(rewrite.get("authority_payload")), rewrite, "visual_qa.metrics.render_payload_used"

    rewrite = build_perceived_value_rewriter(plan)
    return _safe_dict(rewrite.get("authority_payload")), rewrite, "perceived_value_rewriter"


def evaluate_brand_veto_gate(
    *,
    plan: dict[str, Any],
    editorial_qa: dict[str, Any],
    visual_qa: dict[str, Any],
    perceptual_qa: dict[str, Any],
    rubric: RubricEngineResult,
) -> BrandVetoResult:
    visual_qa = _safe_dict(visual_qa)
    hierarchy_gate = _safe_dict(visual_qa.get("hierarchy_gate"))
    dignity_score = _safe_dict(visual_qa.get("brand_dignity_score"))

    authority_payload, rewrite, evaluation_payload_source = _resolve_authority_payload(
        _safe_dict(plan),
        visual_qa,
    )

    text = _normalize(
        " ".join(
            [
                str(authority_payload.get("headline") or ""),
                str(authority_payload.get("hook") or ""),
                str(authority_payload.get("body") or ""),
                str(authority_payload.get("cta") or ""),
                " ".join(str(x) for x in (_safe_list(authority_payload.get("support_points")))),
            ]
        )
    )

    cta_text = _normalize(str(authority_payload.get("cta") or ""))
    rubric_breakdown = _safe_dict(rubric).get("breakdown", {}) if isinstance(rubric, dict) else rubric.breakdown

    commodity = (
        float(rubric_breakdown.get("anti_commodity", 0) or 0) < 8.0
        or "segredo" in text
        or "viral" in text
    )
    cheap_ai = (
        float(rubric_breakdown.get("naturalism", 0) or 0) < 7.8
        or "acredite em você" in text
        or "acredite em voce" in text
        or "mude sua vida" in text
    )
    template = (
        float(rubric_breakdown.get("anti_genericity", 0) or 0) < 8.0
        or "ninguém te conta" in text
        or "ninguem te conta" in text
    )
    prototype = (
        float(visual_qa.get("final_score") or 0) < 78
        or not bool(hierarchy_gate.get("approved", True))
        or not bool(dignity_score.get("approved", True))
    )
    brand_indignity = (
        float(rubric_breakdown.get("brand_fit", 0) or 0) < 8.3
        or float(getattr(rubric, "global_score", 0) or 0) < 8.0
        or "comente aqui" in cta_text
    )

    categories = {
        "commodity": commodity,
        "cheap_ai": cheap_ai,
        "template": template,
        "prototype": prototype,
        "brand_indignity": brand_indignity,
    }
    triggers = [name for name, active in categories.items() if active]

    reasons = [f"brand_veto_payload_source={evaluation_payload_source}"]
    if commodity:
        reasons.append("perceived_value insuficiente ou linguagem commodity")
    if cheap_ai:
        reasons.append("naturalidade insuficiente ou texto com cheiro de IA barata")
    if template:
        reasons.append("anti_commodity insuficiente ou genericidade excessiva")
    if prototype:
        reasons.append("hierarchy insuficiente ou visual ainda com cara de protótipo")
    if brand_indignity:
        reasons.append("brand_fit insuficiente ou global_score insuficiente para dignidade de marca")

    blocked = bool(triggers)
    approved = not blocked
    summary = "brand_veto aprovado no payload pós-rewrite" if approved else "brand_veto bloqueou a peça"

    post_hardening_brand_veto = {
        "visual_score_seen": visual_qa.get("final_score"),
        "hierarchy_approved": hierarchy_gate.get("approved"),
        "brand_dignity_approved": dignity_score.get("approved"),
        "rubric_brand_fit": rubric_breakdown.get("brand_fit"),
        "rubric_global_score": getattr(rubric, "global_score", None),
        "hardening_considered": True,
    }

    return BrandVetoResult(
        approved=approved,
        blocked=blocked,
        categories=categories,
        triggers=triggers,
        reasons=reasons,
        summary=summary,
        evaluation_payload_source=evaluation_payload_source,
        hardening_considered=True,
        post_hardening_brand_veto=post_hardening_brand_veto,
        pre_rewrite_state=rewrite.get("pre_rewrite_state"),
        post_rewrite_state=rewrite.get("post_rewrite_state"),
        raw_payload_vs_rewritten_payload=_safe_dict(rewrite.get("raw_payload_vs_rewritten_payload")),
        rewritten_payload_vs_authorized_payload={},
    )
