from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .brand_veto_gate import BrandVetoResult
from .rubric_engine import RubricEngineResult


TECHNICAL_TEST = "technical_test"
INTERNAL_LAB = "internal_lab"
EDITORIAL_STAGING = "editorial_staging"
BRAND_LIVE = "brand_live"
BLOCKED_QUALITY = "blocked_quality"
BLOCKED_BRAND = "blocked_brand"


@dataclass
class PublicationAuthorizationResult:
    selected_state: str
    supported_states: list[str]
    can_publish_placeholder: bool
    can_publish_real: bool
    brand_live_blocked_by_default: bool
    brand_live_candidate: bool
    reasons: list[str]
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def authorize_publication(
    *,
    force_placeholder: bool,
    editorial_qa: dict[str, Any],
    visual_qa: dict[str, Any],
    perceptual_qa: dict[str, Any],
    rubric: RubricEngineResult,
    brand_veto: BrandVetoResult,
) -> PublicationAuthorizationResult:
    supported_states = [
        TECHNICAL_TEST,
        INTERNAL_LAB,
        EDITORIAL_STAGING,
        BRAND_LIVE,
        BLOCKED_QUALITY,
        BLOCKED_BRAND,
    ]

    reasons: list[str] = []
    brand_live_blocked_by_default = True
    brand_live_candidate = rubric.eligible_for_brand_live and brand_veto.approved

    if force_placeholder:
        reasons.append("placeholder solicitado: rota técnica autorizada apenas para teste")
        return PublicationAuthorizationResult(
            selected_state=TECHNICAL_TEST,
            supported_states=supported_states,
            can_publish_placeholder=True,
            can_publish_real=False,
            brand_live_blocked_by_default=brand_live_blocked_by_default,
            brand_live_candidate=brand_live_candidate,
            reasons=reasons,
            summary="teste técnico permitido; publish de marca continua bloqueado",
        )

    if brand_veto.blocked:
        reasons.extend(brand_veto.reasons)
        return PublicationAuthorizationResult(
            selected_state=BLOCKED_BRAND,
            supported_states=supported_states,
            can_publish_placeholder=False,
            can_publish_real=False,
            brand_live_blocked_by_default=brand_live_blocked_by_default,
            brand_live_candidate=False,
            reasons=reasons,
            summary="peça bloqueada por marca",
        )

    if (
        not bool(editorial_qa.get("approved"))
        or not bool(visual_qa.get("approved"))
        or not bool(perceptual_qa.get("approved"))
        or not rubric.approved_minimum_quality
    ):
        reasons.append("a peça não passou no piso mínimo de qualidade")
        reasons.extend(rubric.reasons)
        return PublicationAuthorizationResult(
            selected_state=BLOCKED_QUALITY,
            supported_states=supported_states,
            can_publish_placeholder=False,
            can_publish_real=False,
            brand_live_blocked_by_default=brand_live_blocked_by_default,
            brand_live_candidate=False,
            reasons=reasons,
            summary="peça bloqueada por qualidade",
        )

    if rubric.global_score < 8.4:
        reasons.append("a peça passou no mínimo, mas ainda é laboratório interno")
        return PublicationAuthorizationResult(
            selected_state=INTERNAL_LAB,
            supported_states=supported_states,
            can_publish_placeholder=False,
            can_publish_real=False,
            brand_live_blocked_by_default=brand_live_blocked_by_default,
            brand_live_candidate=False,
            reasons=reasons,
            summary="peça autorizada apenas para laboratório interno",
        )

    if rubric.global_score < 8.8:
        reasons.append("a peça pode avançar para staging editorial, mas não para live de marca")
        return PublicationAuthorizationResult(
            selected_state=EDITORIAL_STAGING,
            supported_states=supported_states,
            can_publish_placeholder=False,
            can_publish_real=False,
            brand_live_blocked_by_default=brand_live_blocked_by_default,
            brand_live_candidate=False,
            reasons=reasons,
            summary="peça autorizada para staging editorial",
        )

    reasons.append("a peça atingiu nível potencial de brand_live, mas brand_live continua bloqueado por padrão na Onda 3")
    return PublicationAuthorizationResult(
        selected_state=EDITORIAL_STAGING,
        supported_states=supported_states,
        can_publish_placeholder=False,
        can_publish_real=False,
        brand_live_blocked_by_default=brand_live_blocked_by_default,
        brand_live_candidate=brand_live_candidate,
        reasons=reasons,
        summary="brand_live continua bloqueado por padrão; peça fica em staging editorial",
    )
