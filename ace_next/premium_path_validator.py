from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PremiumPathValidationResult:
    ok: bool
    validator_state: str
    approved_path: bool
    current_stage: str
    expected_next_stage: str | None
    blocked_by: list[str]
    reasons: list[str]
    recommendations: list[str]
    signals: dict[str, Any]
    runtime_touched: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PremiumPathValidator:
    """
    Validador final do caminho premium.

    Objetivo:
    - confirmar se a peça percorre a rota premium sem incoerência
    - cruzar PEP, autorização, consistência de marca e QA multimodal
    - não tocar no runtime soberano
    """

    def evaluate(
        self,
        *,
        premium_eligibility_protocol: dict[str, Any] | None = None,
        publication_authorization_gate: dict[str, Any] | None = None,
        brand_consistency_validator: dict[str, Any] | None = None,
        multimodal_reel_qa: dict[str, Any] | None = None,
        format_hint: str | None = None,
    ) -> dict[str, Any]:
        premium_eligibility_protocol = _safe_dict(premium_eligibility_protocol)
        publication_authorization_gate = _safe_dict(publication_authorization_gate)
        brand_consistency_validator = _safe_dict(brand_consistency_validator)
        multimodal_reel_qa = _safe_dict(multimodal_reel_qa)

        format_hint = _clean_text(format_hint or "image").lower()
        current_stage = _clean_text(
            publication_authorization_gate.get("selected_state")
            or premium_eligibility_protocol.get("classification")
            or "unknown"
        ).lower()

        pep_staging = bool(
            premium_eligibility_protocol.get("eligible_for_editorial_staging")
            or premium_eligibility_protocol.get("approved_for_staging")
        )
        pep_brand_live = bool(
            premium_eligibility_protocol.get("eligible_for_brand_live_candidate")
            or premium_eligibility_protocol.get("approved_for_brand_live")
        )
        brand_consistent = bool(brand_consistency_validator.get("approved"))
        multimodal_ready = True

        if format_hint == "reel":
            multimodal_ready = bool(multimodal_reel_qa.get("approved"))

        blocked_by: list[str] = []
        reasons: list[str] = []
        recommendations: list[str] = []

        if not pep_staging and not pep_brand_live:
            blocked_by.append("premium_eligibility_protocol")
            reasons.append("PEP ainda não liberou a peça para a rota premium")
            recommendations.append("corrigir floors soberanos antes de seguir")

        if not brand_consistent:
            blocked_by.append("brand_consistency_validator")
            reasons.append("consistência de marca ainda não foi validada")
            recommendations.append("alinhar assinatura editorial e tom da peça")

        if format_hint == "reel" and not multimodal_ready:
            blocked_by.append("multimodal_reel_qa")
            reasons.append("QA multimodal do reel ainda não aprovou a peça")
            recommendations.append("revisar ritmo, áudio, visual e naturalismo")

        expected_next_stage: str | None = None

        if pep_brand_live and brand_consistent and multimodal_ready:
            expected_next_stage = "brand_live_candidate"
        elif pep_staging and brand_consistent:
            expected_next_stage = "editorial_staging"
        elif pep_staging:
            expected_next_stage = "internal_lab"
        else:
            expected_next_stage = None

        if current_stage == "blocked_brand":
            blocked_by.append("publication_authorization_gate")
            reasons.append("gate de publicação marcou bloqueio de marca")
        elif current_stage == "blocked_quality":
            blocked_by.append("publication_authorization_gate")
            reasons.append("gate de publicação marcou bloqueio de qualidade")

        if expected_next_stage and current_stage and current_stage not in {
            expected_next_stage,
            "brand_live_candidate",
            "brand_live",
        }:
            recommendations.append(
                f"estado atual '{current_stage}' ainda não coincide com a melhor rota '{expected_next_stage}'"
            )

        approved_path = len(_dedupe(blocked_by)) == 0 and expected_next_stage is not None
        if approved_path:
            reasons.append("caminho premium validado sem contradição estrutural")
        else:
            recommendations.append("não ligar esse fluxo no runtime antes de fechar a rota")

        result = PremiumPathValidationResult(
            ok=True,
            validator_state="premium_path_validator_ready",
            approved_path=approved_path,
            current_stage=current_stage or "unknown",
            expected_next_stage=expected_next_stage,
            blocked_by=_dedupe(blocked_by),
            reasons=_dedupe(reasons),
            recommendations=_dedupe(recommendations),
            signals={
                "format_hint": format_hint,
                "pep_staging": pep_staging,
                "pep_brand_live": pep_brand_live,
                "brand_consistent": brand_consistent,
                "multimodal_ready": multimodal_ready,
                "current_stage": current_stage,
            },
            runtime_touched=False,
        )
        return result.to_dict()


def evaluate_premium_path(
    *,
    premium_eligibility_protocol: dict[str, Any] | None = None,
    publication_authorization_gate: dict[str, Any] | None = None,
    brand_consistency_validator: dict[str, Any] | None = None,
    multimodal_reel_qa: dict[str, Any] | None = None,
    format_hint: str | None = None,
) -> dict[str, Any]:
    return PremiumPathValidator().evaluate(
        premium_eligibility_protocol=premium_eligibility_protocol,
        publication_authorization_gate=publication_authorization_gate,
        brand_consistency_validator=brand_consistency_validator,
        multimodal_reel_qa=multimodal_reel_qa,
        format_hint=format_hint,
    )


def premium_path_examples() -> dict[str, Any]:
    return evaluate_premium_path(
        premium_eligibility_protocol={
            "eligible_for_editorial_staging": True,
            "eligible_for_brand_live_candidate": False,
            "classification": "editorial_staging",
        },
        publication_authorization_gate={
            "selected_state": "editorial_staging",
        },
        brand_consistency_validator={
            "approved": True,
        },
        multimodal_reel_qa={
            "approved": True,
        },
        format_hint="image",
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
