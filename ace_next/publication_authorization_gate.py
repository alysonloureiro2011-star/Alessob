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


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class PublicationAuthorizationResult:
    selected_state: str
    supported_states: list[str]
    can_publish_placeholder: bool
    can_publish_real: bool
    brand_live_blocked_by_default: bool
    brand_live_candidate: bool
    main_surface_allowed: bool
    requires_human_review: bool
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
    env_flags: dict[str, Any] | None = None,
    request_flags: dict[str, Any] | None = None,
) -> PublicationAuthorizationResult:
    env_flags = dict(env_flags or {})
    request_flags = dict(request_flags or {})

    supported_states = [
        TECHNICAL_TEST,
        INTERNAL_LAB,
        EDITORIAL_STAGING,
        BRAND_LIVE,
        BLOCKED_QUALITY,
        BLOCKED_BRAND,
    ]

    reasons: list[str] = []
    require_human_review = _as_bool(env_flags.get("ACE_REQUIRE_HUMAN_REVIEW_FOR_BRAND_LIVE"), True)
    brand_live_blocked_by_default = True

    brand_live_candidate = rubric.eligible_for_brand_live and brand_veto.approved
    explicit_brand_live_request = _as_bool(request_flags.get("brand_live_arm"), False)
    human_review_approved = _as_bool(request_flags.get("human_review_approved"), False)

    if force_placeholder:
        reasons.append("placeholder solicitado: rota técnica autorizada apenas para teste")
        return PublicationAuthorizationResult(
            selected_state=TECHNICAL_TEST,
            supported_states=supported_states,
            can_publish_placeholder=True,
            can_publish_real=False,
            brand_live_blocked_by_default=brand_live_blocked_by_default,
            brand_live_candidate=brand_live_candidate,
            main_surface_allowed=False,
            requires_human_review=require_human_review,
            reasons=reasons,
            summary="teste técnico permitido; publish principal continua bloqueado",
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
            main_surface_allowed=False,
            requires_human_review=require_human_review,
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
            main_surface_allowed=False,
            requires_human_review=require_human_review,
            reasons=reasons,
            summary="peça bloqueada por qualidade",
        )

    if rubric.global_score < 8.4:
        reasons.append("a peça passou no mínimo, mas continua em laboratório interno")
        return PublicationAuthorizationResult(
            selected_state=INTERNAL_LAB,
            supported_states=supported_states,
            can_publish_placeholder=False,
            can_publish_real=False,
            brand_live_blocked_by_default=brand_live_blocked_by_default,
            brand_live_candidate=False,
            main_surface_allowed=False,
            requires_human_review=require_human_review,
            reasons=reasons,
            summary="peça autorizada apenas para internal_lab",
        )

    if rubric.global_score < 8.8:
        reasons.append("a peça pode avançar para staging editorial, mas não para superfície principal")
        return PublicationAuthorizationResult(
            selected_state=EDITORIAL_STAGING,
            supported_states=supported_states,
            can_publish_placeholder=False,
            can_publish_real=False,
            brand_live_blocked_by_default=brand_live_blocked_by_default,
            brand_live_candidate=False,
            main_surface_allowed=False,
            requires_human_review=require_human_review,
            reasons=reasons,
            summary="peça autorizada para editorial_staging",
        )

    reasons.append("a peça atingiu candidatura a brand_live, mas a superfície principal continua protegida")
    if require_human_review:
        reasons.append("brand_live exige revisão humana explícita")
    if not explicit_brand_live_request:
        reasons.append("brand_live não foi armado explicitamente")

    can_publish_real = bool(
        explicit_brand_live_request
        and (not require_human_review or human_review_approved)
    )

    return PublicationAuthorizationResult(
        selected_state=BRAND_LIVE,
        supported_states=supported_states,
        can_publish_placeholder=False,
        can_publish_real=can_publish_real,
        brand_live_blocked_by_default=brand_live_blocked_by_default,
        brand_live_candidate=brand_live_candidate,
        main_surface_allowed=can_publish_real,
        requires_human_review=require_human_review,
        reasons=reasons,
        summary="brand_live é o único estado elegível para superfície principal, mas segue protegido por padrão",
    )
