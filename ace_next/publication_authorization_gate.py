from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .brand_veto_gate import BrandVetoResult
from .premium_eligibility_protocol import evaluate_premium_eligibility_protocol
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


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        try:
            return value.to_dict()
        except Exception:
            return {}
    return {}


def _merge_reasons(*reason_lists: Any) -> list[str]:
    merged: list[str] = []
    for item in reason_lists:
        values = item if isinstance(item, list) else [item]
        for value in values:
            text = str(value or "").strip()
            if text and text not in merged:
                merged.append(text)
    return merged


def _state_from_premium_protocol(classification: str) -> str:
    if classification == BLOCKED_BRAND:
        return BLOCKED_BRAND
    if classification == BLOCKED_QUALITY:
        return BLOCKED_QUALITY
    if classification == TECHNICAL_TEST:
        return TECHNICAL_TEST
    if classification == "editorial_staging":
        return EDITORIAL_STAGING
    if classification == "brand_live_candidate":
        return EDITORIAL_STAGING
    return INTERNAL_LAB


def _resolve_staging_hardener(
    visual_qa: dict[str, Any],
    explicit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    explicit_dict = _safe_dict(explicit)
    if explicit_dict:
        return explicit_dict
    metrics = _safe_dict(_safe_dict(visual_qa).get("metrics"))
    return _safe_dict(metrics.get("staging_hardener"))


def _resolve_authority_payload_source(
    visual_qa: dict[str, Any],
    explicit: str | None = None,
) -> str:
    if explicit:
        return str(explicit)
    metrics = _safe_dict(_safe_dict(visual_qa).get("metrics"))
    if _safe_dict(metrics.get("render_payload_used")):
        return "visual_qa.metrics.render_payload_used"
    if _safe_dict(_safe_dict(metrics.get("staging_hardener")).get("hardened_payload")):
        return "visual_qa.metrics.staging_hardener.hardened_payload"
    return "creative_plan"


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
    block_reasons: list[str]
    reasons: list[str]
    summary: str
    premium_protocol: dict[str, Any]
    premium_classification: str
    premium_score: float | None
    eligible_for_editorial_staging: bool
    eligible_for_brand_live_candidate: bool
    staging_hardening_applied: bool
    staging_hardening_report: dict[str, Any]
    pre_hardening_state: str | None
    post_hardening_state: str | None
    authority_payload_source: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _default_gate_payload(
    *,
    selected_state: str,
    supported_states: list[str],
    can_publish_placeholder: bool,
    require_human_review: bool,
    reasons: list[str],
    summary: str,
    premium_protocol: dict[str, Any],
    staging_hardening_applied: bool,
    staging_hardening_report: dict[str, Any],
    pre_hardening_state: str | None,
    post_hardening_state: str | None,
    authority_payload_source: str | None,
) -> PublicationAuthorizationResult:
    blocked_state = selected_state in {BLOCKED_BRAND, BLOCKED_QUALITY}
    brand_live_candidate = bool(premium_protocol.get("eligible_for_brand_live_candidate"))
    return PublicationAuthorizationResult(
        selected_state=selected_state,
        supported_states=supported_states,
        can_publish_placeholder=can_publish_placeholder,
        can_publish_real=False,
        brand_live_blocked_by_default=True,
        brand_live_candidate=brand_live_candidate,
        main_surface_allowed=False,
        requires_human_review=require_human_review,
        block_reasons=reasons if blocked_state else [],
        reasons=reasons,
        summary=summary,
        premium_protocol=premium_protocol,
        premium_classification=str(premium_protocol.get("classification") or selected_state),
        premium_score=premium_protocol.get("premium_score"),
        eligible_for_editorial_staging=bool(premium_protocol.get("eligible_for_editorial_staging")),
        eligible_for_brand_live_candidate=brand_live_candidate,
        staging_hardening_applied=staging_hardening_applied,
        staging_hardening_report=staging_hardening_report,
        pre_hardening_state=pre_hardening_state,
        post_hardening_state=post_hardening_state,
        authority_payload_source=authority_payload_source,
    )


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
    staging_hardener: dict[str, Any] | None = None,
    authority_payload_source: str | None = None,
) -> PublicationAuthorizationResult:
    env_flags = dict(env_flags or {})
    request_flags = dict(request_flags or {})
    visual_qa = _safe_dict(visual_qa)

    supported_states = [
        TECHNICAL_TEST,
        INTERNAL_LAB,
        EDITORIAL_STAGING,
        BRAND_LIVE,
        BLOCKED_QUALITY,
        BLOCKED_BRAND,
    ]

    require_human_review = _as_bool(env_flags.get("ACE_REQUIRE_HUMAN_REVIEW_FOR_BRAND_LIVE"), True)
    resolved_hardener = _resolve_staging_hardener(visual_qa, staging_hardener)
    resolved_source = _resolve_authority_payload_source(visual_qa, authority_payload_source)

    staging_hardening_report = _safe_dict(resolved_hardener.get("hardening_report"))
    staging_hardening_applied = bool(resolved_hardener.get("ok")) or bool(staging_hardening_report)
    pre_hardening_state = "blocked_brand_candidate" if staging_hardening_applied else None

    try:
        premium_protocol = evaluate_premium_eligibility_protocol(
            creative_plan=None,
            editorial_qa=_safe_dict(editorial_qa),
            visual_qa=visual_qa,
            perceptual_qa=_safe_dict(perceptual_qa),
            rubric_engine=_safe_dict(rubric),
            brand_veto_gate=_safe_dict(brand_veto),
            publication_authorization_gate={
                "selected_state": TECHNICAL_TEST if force_placeholder else None,
                "requires_human_review": require_human_review,
                "can_publish_real": False,
                "main_surface_allowed": False,
            },
        )
    except Exception as exc:
        premium_protocol = {
            "ok": False,
            "classification": INTERNAL_LAB,
            "eligible_for_lab": True,
            "eligible_for_editorial_staging": False,
            "eligible_for_brand_live_candidate": False,
            "blocked_by_quality": False,
            "blocked_by_brand": False,
            "requires_human_review": True,
            "brand_live_allowed_now": False,
            "premium_score": None,
            "minimums": {},
            "observed_scores": {},
            "failed_checks": ["premium_protocol_runtime_error"],
            "reasons": [f"premium protocol falhou: {type(exc).__name__}: {exc}"],
            "next_best_state": INTERNAL_LAB,
            "summary": "fallback conservador do premium protocol",
        }

    premium_classification = str(premium_protocol.get("classification") or INTERNAL_LAB)

    if force_placeholder:
        reasons = _merge_reasons(
            "placeholder solicitado: rota técnica autorizada apenas para teste",
            f"authority_payload_source={resolved_source}",
            "staging hardening considerado na autorização" if staging_hardening_applied else None,
            premium_protocol.get("reasons") or [],
        )
        return _default_gate_payload(
            selected_state=TECHNICAL_TEST,
            supported_states=supported_states,
            can_publish_placeholder=True,
            require_human_review=require_human_review,
            reasons=reasons,
            summary="teste técnico permitido; publish principal continua bloqueado",
            premium_protocol=premium_protocol,
            staging_hardening_applied=staging_hardening_applied,
            staging_hardening_report=staging_hardening_report,
            pre_hardening_state=pre_hardening_state,
            post_hardening_state=TECHNICAL_TEST,
            authority_payload_source=resolved_source,
        )

    selected_state = _state_from_premium_protocol(premium_classification)

    if premium_classification == BLOCKED_BRAND:
        reasons = _merge_reasons(
            "peça bloqueada por risco de marca",
            f"authority_payload_source={resolved_source}",
            "staging hardening considerado na autorização" if staging_hardening_applied else None,
            premium_protocol.get("reasons") or [],
            _safe_dict(brand_veto).get("reasons") or [],
        )
        return _default_gate_payload(
            selected_state=BLOCKED_BRAND,
            supported_states=supported_states,
            can_publish_placeholder=False,
            require_human_review=require_human_review,
            reasons=reasons,
            summary="peça bloqueada por risco de marca",
            premium_protocol=premium_protocol,
            staging_hardening_applied=staging_hardening_applied,
            staging_hardening_report=staging_hardening_report,
            pre_hardening_state=pre_hardening_state,
            post_hardening_state=BLOCKED_BRAND,
            authority_payload_source=resolved_source,
        )

    if premium_classification == BLOCKED_QUALITY:
        reasons = _merge_reasons(
            "peça bloqueada por qualidade premium insuficiente",
            f"authority_payload_source={resolved_source}",
            "staging hardening considerado na autorização" if staging_hardening_applied else None,
            premium_protocol.get("reasons") or [],
            _safe_dict(rubric).get("reasons") or [],
        )
        return _default_gate_payload(
            selected_state=BLOCKED_QUALITY,
            supported_states=supported_states,
            can_publish_placeholder=False,
            require_human_review=require_human_review,
            reasons=reasons,
            summary="peça bloqueada por qualidade premium insuficiente",
            premium_protocol=premium_protocol,
            staging_hardening_applied=staging_hardening_applied,
            staging_hardening_report=staging_hardening_report,
            pre_hardening_state=pre_hardening_state,
            post_hardening_state=BLOCKED_QUALITY,
            authority_payload_source=resolved_source,
        )

    if premium_classification == "editorial_staging":
        reasons = _merge_reasons(
            "peça aprovada apenas para editorial_staging",
            f"authority_payload_source={resolved_source}",
            "staging hardening considerado na autorização" if staging_hardening_applied else None,
            premium_protocol.get("reasons") or [],
        )
        return _default_gate_payload(
            selected_state=EDITORIAL_STAGING,
            supported_states=supported_states,
            can_publish_placeholder=False,
            require_human_review=True,
            reasons=reasons,
            summary="peça aprovada apenas para editorial_staging",
            premium_protocol=premium_protocol,
            staging_hardening_applied=staging_hardening_applied,
            staging_hardening_report=staging_hardening_report,
            pre_hardening_state=pre_hardening_state,
            post_hardening_state=EDITORIAL_STAGING,
            authority_payload_source=resolved_source,
        )

    if premium_classification == "brand_live_candidate":
        reasons = _merge_reasons(
            "peça candidata a brand_live, mas ainda sob revisão humana obrigatória",
            "brand_live automático continua proibido",
            f"authority_payload_source={resolved_source}",
            "staging hardening considerado na autorização" if staging_hardening_applied else None,
            premium_protocol.get("reasons") or [],
        )
        return _default_gate_payload(
            selected_state=EDITORIAL_STAGING,
            supported_states=supported_states,
            can_publish_placeholder=False,
            require_human_review=True,
            reasons=reasons,
            summary="peça candidata a brand_live, mas ainda sob revisão humana obrigatória",
            premium_protocol=premium_protocol,
            staging_hardening_applied=staging_hardening_applied,
            staging_hardening_report=staging_hardening_report,
            pre_hardening_state=pre_hardening_state,
            post_hardening_state=EDITORIAL_STAGING,
            authority_payload_source=resolved_source,
        )

    reasons = _merge_reasons(
        f"authority_payload_source={resolved_source}",
        "staging hardening considerado na autorização" if staging_hardening_applied else None,
        premium_protocol.get("reasons") or [],
        _safe_dict(rubric).get("reasons") or [],
    )

    summary = "peça autorizada apenas para internal_lab"
    if selected_state == TECHNICAL_TEST:
        summary = "peça restrita a teste técnico"
    elif premium_classification == INTERNAL_LAB:
        summary = "peça autorizada apenas para internal_lab"

    return _default_gate_payload(
        selected_state=selected_state,
        supported_states=supported_states,
        can_publish_placeholder=False,
        require_human_review=True,
        reasons=reasons or [summary],
        summary=summary,
        premium_protocol=premium_protocol,
        staging_hardening_applied=staging_hardening_applied,
        staging_hardening_report=staging_hardening_report,
        pre_hardening_state=pre_hardening_state,
        post_hardening_state=selected_state,
        authority_payload_source=resolved_source,
    )
