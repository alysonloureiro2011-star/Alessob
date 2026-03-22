from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .rubric_engine import RubricEngineResult


@dataclass
class BrandVetoResult:
    approved: bool
    blocked: bool
    categories: dict[str, bool]
    triggers: list[str]
    reasons: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalize(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def evaluate_brand_veto_gate(
    *,
    plan: dict[str, Any],
    editorial_qa: dict[str, Any],
    visual_qa: dict[str, Any],
    perceptual_qa: dict[str, Any],
    rubric: RubricEngineResult,
) -> BrandVetoResult:
    editorial_flags = list(editorial_qa.get("flags") or [])
    perceptual_metrics = perceptual_qa.get("metrics") or {}

    text = _normalize(
        " ".join(
            [
                str(plan.get("headline") or ""),
                str(plan.get("hook") or ""),
                str(plan.get("body") or ""),
                str(plan.get("cta") or ""),
                " ".join(str(x) for x in (plan.get("support_points") or [])),
            ]
        )
    )

    commodity = (
        rubric.breakdown.get("anti_commodity", 0) < 8.0
        or any(term in text for term in ["viral", "imperdível", "segredo", "fórmula"])
    )
    cheap_ai = (
        rubric.breakdown.get("naturalism", 0) < 7.5
        or "cheap_ai_tone" in editorial_flags
        or "coach_generic" in editorial_flags
    )
    template = (
        rubric.breakdown.get("anti_genericity", 0) < 8.0
        or "commodity_language" in editorial_flags
    )
    prototype = (
        not bool(perceptual_metrics.get("zero_overlap"))
        or rubric.breakdown.get("legibility", 0) < 7.0
        or rubric.breakdown.get("composition", 0) < 7.0
        or rubric.breakdown.get("contrast", 0) < 7.0
        or int(visual_qa.get("final_score") or 0) < int(visual_qa.get("minimum_score") or 75)
    )
    brand_indignity = (
        commodity
        or cheap_ai
        or template
        or prototype
        or rubric.breakdown.get("brand_fit", 0) < 8.5
        or rubric.global_score < 7.5
    )

    categories = {
        "commodity": commodity,
        "cheap_ai": cheap_ai,
        "template": template,
        "prototype": prototype,
        "brand_indignity": brand_indignity,
    }

    triggers = [name for name, active in categories.items() if active]

    reasons: list[str] = []
    if commodity:
        reasons.append("a peça foi classificada como commodity ou com linguagem de commodity")
    if cheap_ai:
        reasons.append("a peça foi classificada como IA barata ou naturalidade insuficiente")
    if template:
        reasons.append("a peça foi classificada como template/genericidade excessiva")
    if prototype:
        reasons.append("a peça foi classificada como protótipo visual insuficiente")
    if brand_indignity:
        reasons.append("a peça não atingiu dignidade mínima de marca")

    blocked = bool(triggers)
    approved = not blocked

    if approved:
        summary = "brand_veto aprovado"
        reasons.append("nenhum veto de marca foi disparado")
    else:
        summary = "brand_veto bloqueou a peça"

    return BrandVetoResult(
        approved=approved,
        blocked=blocked,
        categories=categories,
        triggers=triggers,
        reasons=reasons,
        summary=summary,
    )
