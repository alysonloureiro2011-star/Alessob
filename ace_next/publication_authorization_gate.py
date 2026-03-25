from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .authorization_hardening_pack import (
    build_observed_scores,
    build_payload_comparison,
    build_promotion_readiness_summary,
    decide_publication_state,
)
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
    missing_for_brand_live: list[str]
    score_gap_to_brand_live: float
    next_quality_lift_targets: list[dict[str, Any]]
    promotion_readiness_summary: dict[str, Any]
    pre_rewrite_state: str | None
    post_rewrite_state: str | None
    raw_payload_vs_rewritten_payload: dict[str, Any]
    rewritten_payload_vs_authorized_payload: dict[str, Any]

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

    rubric_dict = _safe_dict(rubric)
    brand_veto_dict = _safe_dict(brand_veto)
    rubric_breakdown = _safe_dict(rubric_dict.get("breakdown"))
    post_hardening_scores = _safe_dict(rubric_dict.get("post_hardening_scores"))

    observed_scores = build_observed_scores(
        rubric_breakdown=rubric_breakdown,
        global_score=rubric_dict.get("global_score"),
        post_hardening_scores=post_hardening_scores,
    )

    decision = decide_publication_state(
        force_placeholder=force_placeholder,
        observed_scores=observed_scores,
        brand_veto_blocked=bool(brand_veto_dict.get("blocked")),
        require_human_review=require_human_review,
    )

    promotion_readiness_summary = build_promotion_readiness_summary(
        observed_scores=observed_scores,
        brand_veto_blocked=bool(brand_veto_dict.get("blocked")),
        current_classification=decision["classification"],
    )

    raw_vs_rewritten = _safe_dict(rubric_dict.get("raw_payload_vs_rewritten_payload"))
    rewritten_payload_vs_authorized_payload = build_payload_comparison(
        raw_payload={},
        rewritten_payload={"state": rubric_dict.get("post_rewrite_state")},
        authorized_payload={
            "state": decision["selected_state"],
            "classification": decision["classification"],
        },
    )

    reasons = _merge_reasons(
        decision["reasons"],
        rubric_dict.get("reasons") or [],
        brand_veto_dict.get("reasons") or [],
    )

    premium_protocol = {
        "ok": True,
        "classification": decision["classification"],
        "eligible_for_lab": decision["classification"] in {TECHNICAL_TEST, INTERNAL_LAB, EDITORIAL_STAGING, "brand_live_candidate", BRAND_LIVE},
        "eligible_for_editorial_staging": decision["eligible_for_editorial_staging"],
        "eligible_for_brand_live_candidate": decision["eligible_for_brand_live_candidate"],
        "blocked_by_quality": decision["classification"] == BLOCKED_QUALITY,
        "blocked_by_brand": decision["classification"] == BLOCKED_BRAND,
        "requires_human_review": require_human_review,
        "brand_live_allowed_now": False,
        "premium_score": rubric_dict.get("global_score"),
        "observed_scores": observed_scores,
        "failed_checks": (
            decision["failed_staging_floors"]
            + decision["failed_brand_live_floors"]
            + decision["failed_veto_floors"]
        ),
        "reasons": reasons,
        "next_best_state": decision["selected_state"],
        "summary": decision["summary"],
    }

    block_reasons = []
    if decision["classification"] in {BLOCKED_BRAND, BLOCKED_QUALITY}:
        block_reasons = reasons

    return PublicationAuthorizationResult(
        selected_state=decision["selected_state"],
        supported_states=supported_states,
        can_publish_placeholder=force_placeholder,
        can_publish_real=False,
        brand_live_blocked_by_default=True,
        brand_live_candidate=decision["brand_live_candidate"],
        main_surface_allowed=False,
        requires_human_review=require_human_review,
        block_reasons=block_reasons,
        reasons=reasons,
        summary=decision["summary"],
        premium_protocol=premium_protocol,
        premium_classification=decision["classification"],
        premium_score=rubric_dict.get("global_score"),
        eligible_for_editorial_staging=decision["eligible_for_editorial_staging"],
        eligible_for_brand_live_candidate=decision["eligible_for_brand_live_candidate"],
        staging_hardening_applied=True,
        staging_hardening_report=_safe_dict(staging_hardener),
        pre_hardening_state=rubric_dict.get("pre_hardening_state"),
        post_hardening_state=decision["selected_state"],
        authority_payload_source=authority_payload_source or rubric_dict.get("authority_payload_source"),
        missing_for_brand_live=decision["missing_for_brand_live"],
        score_gap_to_brand_live=decision["score_gap_to_brand_live"],
        next_quality_lift_targets=decision["next_quality_lift_targets"],
        promotion_readiness_summary=promotion_readiness_summary,
        pre_rewrite_state=rubric_dict.get("pre_rewrite_state"),
        post_rewrite_state=rubric_dict.get("post_rewrite_state"),
        raw_payload_vs_rewritten_payload=raw_vs_rewritten,
        rewritten_payload_vs_authorized_payload=rewritten_payload_vs_authorized_payload,
    )
