from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BrandConsistencyResult:
    ok: bool
    validator_state: str
    approved: bool
    consistency_score: float
    blocked_by: list[str]
    reasons: list[str]
    recommendations: list[str]
    signals: dict[str, Any]
    runtime_touched: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BrandConsistencyValidator:
    """
    Camada final de validação de marca e consistência.

    Objetivo:
    - verificar coerência entre plano, saída visual e gates premium
    - travar deriva de marca antes da ligação única no runtime
    - não publicar, não alterar política e não tocar no runtime soberano
    """

    def evaluate(
        self,
        *,
        creative_plan: dict[str, Any] | None = None,
        rubric_engine: dict[str, Any] | None = None,
        brand_veto_gate: dict[str, Any] | None = None,
        premium_eligibility_protocol: dict[str, Any] | None = None,
        brand_context: dict[str, Any] | None = None,
        serial_continuity: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        creative_plan = _safe_dict(creative_plan)
        rubric_engine = _safe_dict(rubric_engine)
        brand_veto_gate = _safe_dict(brand_veto_gate)
        premium_eligibility_protocol = _safe_dict(premium_eligibility_protocol)
        brand_context = _safe_dict(brand_context)
        serial_continuity = _safe_dict(serial_continuity)

        breakdown = _safe_dict(rubric_engine.get("breakdown"))
        brand_surface_mode = _clean_text(
            brand_context.get("brand_surface_mode")
            or brand_context.get("surface_mode")
            or "protected"
        ).lower()
        headline = _clean_text(creative_plan.get("headline"))
        hook = _clean_text(creative_plan.get("hook"))
        cta = _clean_text(creative_plan.get("cta"))
        topic_seed = _clean_text(creative_plan.get("topic_seed") or creative_plan.get("trend") or headline)
        series_name = _clean_text(serial_continuity.get("series_name"))
        next_episode_seed = _clean_text(serial_continuity.get("next_episode_seed"))

        brand_fit = _safe_float(breakdown.get("brand_fit"), default=0.0)
        authority = _safe_float(breakdown.get("authority"), default=0.0)
        anti_genericity = _safe_float(breakdown.get("anti_genericity"), default=0.0)
        anti_commodity = _safe_float(breakdown.get("anti_commodity"), default=0.0)
        pep_approved = bool(premium_eligibility_protocol.get("eligible_for_editorial_staging") or premium_eligibility_protocol.get("eligible_for_brand_live_candidate"))
        veto_blocked = bool(brand_veto_gate.get("blocked"))

        blocked_by: list[str] = []
        reasons: list[str] = []
        recommendations: list[str] = []

        if veto_blocked:
            blocked_by.append("brand_veto_gate")
            reasons.append("brand veto já bloqueou a peça")

        if brand_fit < 8.3:
            blocked_by.append("brand_fit")
            reasons.append("brand_fit abaixo do piso de consistência")
            recommendations.append("reforçar assinatura editorial e linguagem proprietária")

        if authority < 8.0:
            blocked_by.append("authority")
            reasons.append("autoridade percebida abaixo do piso")
            recommendations.append("aumentar precisão causal e reduzir formulação genérica")

        if anti_genericity < 8.0:
            blocked_by.append("anti_genericity")
            reasons.append("texto ainda genérico para a superfície da marca")
            recommendations.append("trocar frases de molde por formulação mais proprietária")

        if anti_commodity < 8.0:
            blocked_by.append("anti_commodity")
            reasons.append("peça ainda próxima de commodity")
            recommendations.append("elevar singularidade editorial e densidade útil")

        if not pep_approved:
            blocked_by.append("premium_eligibility_protocol")
            reasons.append("PEP ainda não liberou a peça para staging")

        if brand_surface_mode not in {"protected", "premium", "staging"}:
            blocked_by.append("brand_surface_mode")
            reasons.append("surface mode fora do regime premium esperado")

        if cta and any(token in cta.lower() for token in {"comente aqui", "marca alguém", "marca alguem", "corre"}):
            blocked_by.append("cta_brand_drift")
            reasons.append("CTA puxa a peça para um comportamento fora da dignidade da marca")
            recommendations.append("usar CTA de save/share/revisita mais sóbrio")

        if series_name and next_episode_seed and topic_seed and topic_seed.lower() not in next_episode_seed.lower():
            recommendations.append("alinhar próxima continuidade ao tema raiz da série")

        consistency_score = round(
            (
                brand_fit * 0.35
                + authority * 0.20
                + anti_genericity * 0.20
                + anti_commodity * 0.15
                + (8.6 if pep_approved else 6.0) * 0.10
            ),
            2,
        )

        approved = len(blocked_by) == 0 and consistency_score >= 8.2
        if approved:
            reasons.append("peça coerente com a assinatura premium atual")
        else:
            recommendations.append("revalidar peça antes da ligação no runtime")

        result = BrandConsistencyResult(
            ok=True,
            validator_state="brand_consistency_validator_ready",
            approved=approved,
            consistency_score=consistency_score,
            blocked_by=_dedupe(blocked_by),
            reasons=_dedupe(reasons),
            recommendations=_dedupe(recommendations),
            signals={
                "brand_surface_mode": brand_surface_mode,
                "topic_seed": topic_seed,
                "series_name": series_name,
                "next_episode_seed": next_episode_seed,
                "headline": headline,
                "hook": hook,
                "cta": cta,
                "brand_fit": brand_fit,
                "authority": authority,
                "anti_genericity": anti_genericity,
                "anti_commodity": anti_commodity,
                "pep_approved": pep_approved,
                "veto_blocked": veto_blocked,
            },
            runtime_touched=False,
        )
        return result.to_dict()


def evaluate_brand_consistency(
    *,
    creative_plan: dict[str, Any] | None = None,
    rubric_engine: dict[str, Any] | None = None,
    brand_veto_gate: dict[str, Any] | None = None,
    premium_eligibility_protocol: dict[str, Any] | None = None,
    brand_context: dict[str, Any] | None = None,
    serial_continuity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return BrandConsistencyValidator().evaluate(
        creative_plan=creative_plan,
        rubric_engine=rubric_engine,
        brand_veto_gate=brand_veto_gate,
        premium_eligibility_protocol=premium_eligibility_protocol,
        brand_context=brand_context,
        serial_continuity=serial_continuity,
    )


def brand_consistency_examples() -> dict[str, Any]:
    return evaluate_brand_consistency(
        creative_plan={
            "topic_seed": "clareza, disciplina e direção",
            "headline": "Você não está sem direção. Está sem estrutura.",
            "hook": "Clareza não nasce do nada. Ela nasce de corte.",
            "cta": "Salve para revisar depois.",
        },
        rubric_engine={
            "breakdown": {
                "brand_fit": 8.7,
                "authority": 8.4,
                "anti_genericity": 8.3,
                "anti_commodity": 8.4,
            }
        },
        brand_veto_gate={"blocked": False},
        premium_eligibility_protocol={"eligible_for_editorial_staging": True},
        brand_context={"brand_surface_mode": "protected"},
        serial_continuity={
            "series_name": "clareza estrutural",
            "next_episode_seed": "clareza estrutural aplicada ao foco",
        },
    )


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            parsed = value.to_dict()
            return dict(parsed) if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _safe_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        key = _clean_text(item).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(_clean_text(item))
    return ordered
