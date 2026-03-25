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
    evaluation_payload_source: str | None
    hardening_considered: bool
    post_hardening_brand_veto: dict[str, Any]

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
) -> tuple[dict[str, Any], str, dict[str, Any]]:
    visual_qa = _safe_dict(visual_qa)
    metrics = _safe_dict(visual_qa.get("metrics"))

    render_payload_used = _safe_dict(metrics.get("render_payload_used"))
    if render_payload_used:
        return render_payload_used, "visual_qa.metrics.render_payload_used", _safe_dict(metrics.get("staging_hardener"))

    staging_hardener = _safe_dict(metrics.get("staging_hardener"))
    hardened_payload = _safe_dict(staging_hardener.get("hardened_payload"))
    if hardened_payload:
        return hardened_payload, "visual_qa.metrics.staging_hardener.hardened_payload", staging_hardener

    return _safe_dict(plan), "creative_plan", staging_hardener


def evaluate_brand_veto_gate(
    *,
    plan: dict[str, Any],
    editorial_qa: dict[str, Any],
    visual_qa: dict[str, Any],
    perceptual_qa: dict[str, Any],
    rubric: RubricEngineResult,
) -> BrandVetoResult:
    visual_qa = _safe_dict(visual_qa)
    perceptual_qa = _safe_dict(perceptual_qa)
    hierarchy_gate = _safe_dict(visual_qa.get("hierarchy_gate"))
    dignity_score = _safe_dict(visual_qa.get("brand_dignity_score"))

    authority_payload, evaluation_payload_source, staging_hardener = _resolve_authority_payload(
        _safe_dict(plan),
        visual_qa,
    )
    hardening_considered = bool(staging_hardener) or evaluation_payload_source != "creative_plan"

    editorial_flags = list(_safe_dict(editorial_qa).get("flags") or [])
    perceptual_metrics = _safe_dict(perceptual_qa.get("metrics"))

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
    visual_score = float(visual_qa.get("final_score") or 0)
    hierarchy_approved = bool(hierarchy_gate.get("approved"))
    dignity_approved = bool(dignity_score.get("approved"))

    generic_phrase = any(term in text for term in ["segredo", "ninguém te conta", "ninguem te conta", "viral", "imperdível", "imperdivel"])
    cheap_cta = any(term in cta_text for term in ["comente aqui", "corre", "agora", "chama na dm", "clica no link agora"])

    commodity = (
        rubric.breakdown.get("anti_commodity", 0) < 8.0
        or generic_phrase
    )
    cheap_ai = (
        rubric.breakdown.get("naturalism", 0) < 7.5
        or "cheap_ai_tone" in editorial_flags
        or "coach_generic" in editorial_flags
        or dignity_score.get("classification") == "brand_indignity"
    )
    template = (
        rubric.breakdown.get("anti_genericity", 0) < 8.0
        or "commodity_language" in editorial_flags
        or generic_phrase
    )
    prototype = (
        visual_score < 78
        or not hierarchy_approved
        or not dignity_approved
        or not bool(perceptual_metrics.get("zero_overlap", True))
    )

    staging_ready_after_hardening = (
        rubric.breakdown.get("brand_fit", 0) >= 8.3
        and rubric.global_score >= 8.0
        and hierarchy_approved
        and dignity_approved
        and not cheap_cta
        and not generic_phrase
    )

    brand_indignity = (
        commodity
        or cheap_ai
        or template
        or prototype
        or rubric.breakdown.get("brand_fit", 0) < 8.3
        or rubric.global_score < 8.0
    )

    if staging_ready_after_hardening:
        prototype = False
        brand_indignity = False

    categories = {
        "commodity": commodity,
        "cheap_ai": cheap_ai,
        "template": template,
        "prototype": prototype,
        "brand_indignity": brand_indignity,
    }

    triggers = [name for name, active in categories.items() if active]

    reasons: list[str] = [f"brand_veto_payload_source={evaluation_payload_source}"]
    if commodity:
        reasons.append("a peça foi classificada como commodity ou com linguagem de commodity")
    if cheap_ai:
        reasons.append("a peça foi classificada como IA barata ou naturalidade insuficiente")
    if template:
        reasons.append("a peça foi classificada como template/genericidade excessiva")
    if prototype:
        reasons.append("a peça foi classificada como protótipo visual insuficiente")
    if brand_indignity:
        reasons.append("a peça não atingiu dignidade mínima de marca no estado pós-hardening")
    if hardening_considered:
        reasons.append("brand veto considerou a peça endurecida como autoridade")

    blocked = bool(triggers)
    approved = not blocked

    if approved:
        summary = "brand_veto aprovado no payload pós-hardening"
        reasons.append("nenhum veto de marca foi disparado")
    else:
        summary = "brand_veto bloqueou a peça"

    post_hardening_brand_veto = {
        "visual_score_seen": visual_score,
        "hierarchy_approved": hierarchy_approved,
        "brand_dignity_approved": dignity_approved,
        "rubric_brand_fit": rubric.breakdown.get("brand_fit"),
        "rubric_global_score": rubric.global_score,
        "staging_ready_after_hardening": staging_ready_after_hardening,
        "hardening_considered": hardening_considered,
    }

    return BrandVetoResult(
        approved=approved,
        blocked=blocked,
        categories=categories,
        triggers=triggers,
        reasons=reasons,
        summary=summary,
        evaluation_payload_source=evaluation_payload_source,
        hardening_considered=hardening_considered,
        post_hardening_brand_veto=post_hardening_brand_veto,
    )
