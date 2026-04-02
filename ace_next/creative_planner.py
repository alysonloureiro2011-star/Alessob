from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .creative_planner_soberano_v1 import build_creative_plan_soberano_v1
from .reel_retention_policy import evaluate_reel_retention_policy

SERIES_NAME = "Liberta a Verdade"
PUBLISH_STYLE = "official_next_visual_foundation_v1"

STUDY_TAGS = {
    "hook_opening": "0_3s",
    "pattern_interrupt": "3_5s",
    "priority_signals": [
        "save_rate",
        "share_rate",
        "completion_rate",
        "retention_rate",
        "watch_time_ms",
        "replay_rate",
    ],
    "naturalism": "micro_expression_breathing_grain",
    "cinematic": "9x16_rule_of_thirds_bokeh_color_foley_ducking",
    "algorithmic_priority": "shares_saves_completion_watch_time",
}


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _merge_notes(*groups: Any) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in _safe_list(group):
            text = _clean_text(item)
            if text and text not in merged:
                merged.append(text)
    return merged


def _merge_flags(*groups: Any) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in _safe_list(group):
            text = _clean_text(item)
            if text and text not in merged:
                merged.append(text)
    return merged


def _recent_memory_hint(recent_memory: list[dict[str, Any]] | None) -> dict[str, Any]:
    recent = _safe_list(recent_memory)[-5:]
    if not recent:
        return {
            "has_recent_memory": False,
            "latest_hook": None,
            "latest_format": None,
            "latest_style": None,
            "latest_timing_hypothesis": None,
        }

    latest = _safe_dict(recent[-1])
    latest_plan = _safe_dict(latest.get("creative_plan"))
    distribution_context = _safe_dict(
        latest_plan.get("distribution_context") or latest.get("distribution_context")
    )

    return {
        "has_recent_memory": True,
        "latest_hook": latest_plan.get("hook"),
        "latest_format": latest_plan.get("publish_format_now"),
        "latest_style": latest_plan.get("publish_style"),
        "latest_timing_hypothesis": latest_plan.get("timing_hypothesis")
        or distribution_context.get("recommended_timing_hypothesis"),
    }


@dataclass
class CreativePlan:
    ok: bool = True
    topic_seed: str = ""
    problem: str = ""
    insight: str = ""
    angle: str = ""
    hook_family: str = ""
    hook: str = ""
    headline: str = ""
    body: str = ""
    support_points: list[str] = field(default_factory=list)
    narrative_tension: str = ""
    payoff: str = ""
    cta: str = ""
    caption: str = ""
    format_recommendation: str = "image"
    strategic_target_format: str = "image"
    publish_format_now: str = "image"
    publish_style: str = PUBLISH_STYLE
    goal: str = "authority"
    hypothesis: str | None = None
    series_name: str = SERIES_NAME
    continuation_candidate: bool = False
    sequel_potential: str = "medium"
    brand_lexicon_hits: list[str] = field(default_factory=list)
    brand_fit_signals: list[str] = field(default_factory=list)
    anti_generic_risk: str = "low"
    perceived_value_hypothesis: str = ""
    timing_hypothesis: str | None = None
    planner_version: str = "creative_planner_consolidated_v1"
    planner_mode: str = "runtime_consolidated"
    deterministic: bool = False
    deterministic_path: bool = False
    serial_continuity: dict[str, Any] = field(default_factory=dict)
    distribution_context: dict[str, Any] = field(default_factory=dict)
    critic: dict[str, Any] = field(default_factory=dict)
    editorial_critic: dict[str, Any] = field(default_factory=dict)
    caption_gate: dict[str, Any] = field(default_factory=dict)
    planner_selected: str = "creative_planner_consolidated_v1"
    llm_status: dict[str, Any] = field(default_factory=dict)
    fallback_flags: list[str] = field(default_factory=list)
    official_path_quality_state: str = "approved"
    notes: list[str] = field(default_factory=list)
    mission_context: dict[str, Any] = field(default_factory=dict)
    study_tags: dict[str, Any] = field(default_factory=lambda: dict(STUDY_TAGS))
    ethical_boundary: str = "retention_without_hidden_manipulation"
    retention_policy: dict[str, Any] = field(default_factory=dict)
    retention_score: float = 0.0
    premium_eligibility_score: float = 0.0
    publish_ready: bool = False
    veto_reasons: list[str] = field(default_factory=list)
    lift_targets: list[str] = field(default_factory=list)
    study_axes_applied: list[str] = field(default_factory=list)
    memory_override: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _build_caption(headline: str, body: str, cta: str) -> str:
    parts = [_clean_text(headline), _clean_text(body), _clean_text(cta)]
    return "\n\n".join([part for part in parts if part])


def _official_path_quality_state(
    *,
    critic: dict[str, Any],
    retention_policy: dict[str, Any],
) -> str:
    critic = _safe_dict(critic)
    caption_gate = _safe_dict(critic.get("caption_gate"))
    veto_reasons = _safe_list(retention_policy.get("veto_reasons"))
    retention_signal_ready = bool(retention_policy.get("publish_ready"))

    if veto_reasons:
        return "blocked_retention_gate"
    if retention_signal_ready and critic.get("approved") and caption_gate.get("approved"):
        return "approved"
    if critic.get("failed_floors"):
        return "needs_rewrite"
    return "needs_rewrite"


def _retention_policy_payload(
    *,
    sovereign: dict[str, Any],
    publish_format_now: str,
    publish_style: str,
    timing_hypothesis: str | None,
    recent_memory: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    recent_hint = _recent_memory_hint(recent_memory)
    notes = _merge_notes(
        sovereign.get("notes"),
        [
            "hook_opening_0_3s_required",
            "pattern_interrupt_3_5s_required",
            "naturalismo_real_v2_required",
            "cta_deve_priorizar_save_share",
        ],
    )

    if recent_hint.get("has_recent_memory"):
        notes.append("planner_memory_informed=true")

    support_points = [
        str(item) for item in _safe_list(sovereign.get("support_points")) if _clean_text(item)
    ]

    return {
        "hook": sovereign.get("hook"),
        "headline": sovereign.get("headline"),
        "angle": sovereign.get("angle"),
        "body": sovereign.get("body"),
        "cta": sovereign.get("cta"),
        "support_points": support_points,
        "notes": notes,
        "visual_style": "cinematic_natural_editorial",
        "publish_style": publish_style,
        "color_profile": "cinematic_vertical_premium",
        "publish_format_now": publish_format_now,
        "strategic_target_format": sovereign.get("strategic_target_format") or publish_format_now,
        "timing_hypothesis": timing_hypothesis,
    }


def _map_soberano_to_creative_plan(
    trend: str,
    sovereign: dict[str, Any],
    overrides: dict[str, Any] | None = None,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
) -> CreativePlan:
    sovereign = _safe_dict(sovereign)
    overrides = _safe_dict(overrides)
    mission_decision = _safe_dict(mission_decision)
    recent_hint = _recent_memory_hint(recent_memory)

    publish_format_now = (
        _clean_text(overrides.get("publish_format_now"))
        or _clean_text(sovereign.get("format_recommendation"))
        or _clean_text(mission_decision.get("content_type"))
        or "image"
    ).lower()

    publish_style = (
        _clean_text(overrides.get("publish_style"))
        or _clean_text(sovereign.get("publish_style"))
        or PUBLISH_STYLE
    )

    goal = (
        _clean_text(overrides.get("goal"))
        or _clean_text(sovereign.get("goal"))
        or _clean_text(mission_decision.get("goal"))
        or "authority"
    )

    hypothesis = (
        overrides.get("hypothesis")
        or sovereign.get("hypothesis")
        or mission_decision.get("hypothesis")
    )

    timing_hypothesis = (
        overrides.get("timing_hypothesis")
        or sovereign.get("timing_hypothesis")
        or _safe_dict(sovereign.get("distribution_context")).get("timing_hypothesis")
        or recent_hint.get("latest_timing_hypothesis")
    )

    retention_payload = _retention_policy_payload(
        sovereign=sovereign,
        publish_format_now=publish_format_now,
        publish_style=publish_style,
        timing_hypothesis=timing_hypothesis,
        recent_memory=recent_memory,
    )
    retention_policy = evaluate_reel_retention_policy(retention_payload)
    retention_signal_ready = bool(retention_policy.get("publish_ready"))

    critic = _safe_dict(sovereign.get("critic"))
    official_quality_state = _official_path_quality_state(
        critic=critic,
        retention_policy=retention_policy,
    )
    official_publish_ready = official_quality_state == "approved"

    notes = _merge_notes(
        sovereign.get("notes"),
        [
            "planner_selected=creative_planner_consolidated_v1",
            f"official_path_quality_state={official_quality_state}",
            f"retention_signal_ready={retention_signal_ready}",
            f"official_publish_ready={official_publish_ready}",
            "studies_applied=hook_rhythm_naturalism_cinematic_algorithmic_priority",
        ],
    )

    fallback_flags = _merge_flags(
        sovereign.get("fallback_flags"),
        [] if retention_signal_ready else ["retention_signal_not_ready"],
        [] if official_publish_ready else ["official_quality_not_ready"],
    )

    mission_context = {
        "goal": mission_decision.get("goal"),
        "hypothesis": mission_decision.get("hypothesis"),
        "content_type": mission_decision.get("content_type"),
        "priority": mission_decision.get("priority"),
        "confidence": mission_decision.get("confidence"),
        "performance_informed": bool(recent_hint.get("has_recent_memory")),
    }

    return CreativePlan(
        ok=bool(sovereign.get("ok", True)),
        topic_seed=_clean_text(sovereign.get("topic_seed") or trend),
        problem=_clean_text(sovereign.get("problem")),
        insight=_clean_text(sovereign.get("insight")),
        angle=_clean_text(sovereign.get("angle")),
        hook_family=_clean_text(sovereign.get("hook_family")),
        hook=_clean_text(sovereign.get("hook")),
        headline=_clean_text(sovereign.get("headline")),
        body=_clean_text(sovereign.get("body")),
        support_points=[str(item) for item in _safe_list(sovereign.get("support_points"))],
        narrative_tension=_clean_text(sovereign.get("narrative_tension")),
        payoff=_clean_text(sovereign.get("payoff")),
        cta=_clean_text(sovereign.get("cta")),
        caption=_build_caption(
            _clean_text(sovereign.get("headline")),
            _clean_text(sovereign.get("body")),
            _clean_text(sovereign.get("cta")),
        ),
        format_recommendation=_clean_text(sovereign.get("format_recommendation") or publish_format_now),
        strategic_target_format=_clean_text(
            sovereign.get("strategic_target_format") or sovereign.get("format_recommendation") or publish_format_now
        ),
        publish_format_now=publish_format_now,
        publish_style=publish_style,
        goal=goal,
        hypothesis=hypothesis,
        series_name=_clean_text(sovereign.get("series_name") or SERIES_NAME),
        continuation_candidate=bool(sovereign.get("continuation_candidate")),
        sequel_potential=_clean_text(sovereign.get("sequel_potential") or "medium"),
        brand_lexicon_hits=[str(item) for item in _safe_list(sovereign.get("brand_lexicon_hits"))],
        brand_fit_signals=[str(item) for item in _safe_list(sovereign.get("brand_fit_signals"))],
        anti_generic_risk=_clean_text(sovereign.get("anti_generic_risk") or "low"),
        perceived_value_hypothesis=_clean_text(sovereign.get("perceived_value_hypothesis")),
        timing_hypothesis=timing_hypothesis,
        planner_version="creative_planner_consolidated_v1",
        planner_mode=_clean_text(sovereign.get("planner_mode") or "runtime_consolidated"),
        deterministic=bool(sovereign.get("deterministic", False)),
        deterministic_path=bool(sovereign.get("deterministic_path", False)),
        serial_continuity=_safe_dict(sovereign.get("serial_continuity")),
        distribution_context=_safe_dict(sovereign.get("distribution_context")),
        critic=critic,
        editorial_critic=_safe_dict(sovereign.get("editorial_critic") or critic),
        caption_gate=_safe_dict(sovereign.get("caption_gate") or critic.get("caption_gate")),
        planner_selected="creative_planner_consolidated_v1",
        llm_status=_safe_dict(sovereign.get("llm_status")),
        fallback_flags=fallback_flags,
        official_path_quality_state=official_quality_state,
        notes=notes,
        mission_context=mission_context,
        study_tags=dict(STUDY_TAGS),
        ethical_boundary="retention_without_hidden_manipulation",
        retention_policy=retention_policy,
        retention_score=float(retention_policy.get("premium_eligibility_score") or 0.0),
        premium_eligibility_score=float(retention_policy.get("premium_eligibility_score") or 0.0),
        publish_ready=official_publish_ready,
        veto_reasons=[str(item) for item in _safe_list(retention_policy.get("veto_reasons"))],
        lift_targets=[str(item) for item in _safe_list(retention_policy.get("lift_targets"))],
        study_axes_applied=[str(item) for item in _safe_list(retention_policy.get("study_axes_applied"))],
        memory_override=False,
    )


def _build_creative_plan_legacy(
    trend: str,
    overrides: dict[str, Any] | None = None,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
) -> CreativePlan:
    overrides = _safe_dict(overrides)
    mission_decision = _safe_dict(mission_decision)

    sovereign = build_creative_plan_soberano_v1(
        topic_seed=trend,
        signal_context={
            "source": "creative_planner_legacy",
            "mission_context": mission_decision,
            "recent_content": _safe_list(recent_memory),
            "study_tags": dict(STUDY_TAGS),
        },
        brand_context={
            "series_name": SERIES_NAME,
            "surface": "instagram_reels",
            "account": "@libertaverdades",
            "publish_style": overrides.get("publish_style") or PUBLISH_STYLE,
            "goal": overrides.get("goal") or mission_decision.get("goal"),
        },
        format_hint=overrides.get("publish_format_now") or mission_decision.get("content_type"),
    )

    plan = _map_soberano_to_creative_plan(
        trend,
        sovereign,
        overrides=overrides,
        mission_decision=mission_decision,
        recent_memory=recent_memory,
    )
    plan.notes.append("planner_path=legacy_compatibility")
    if "legacy_compatibility" not in plan.fallback_flags:
        plan.fallback_flags.append("legacy_compatibility")
    return plan


def build_creative_plan(
    trend: str,
    overrides: dict[str, Any] | None = None,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
) -> CreativePlan:
    overrides = _safe_dict(overrides)
    mission_decision = _safe_dict(mission_decision)
    recent_memory = _safe_list(recent_memory)

    sovereign = build_creative_plan_soberano_v1(
        topic_seed=trend,
        signal_context={
            "source": "creative_planner_consolidated",
            "mission_context": mission_decision,
            "recent_content": recent_memory[-5:],
            "study_tags": dict(STUDY_TAGS),
        },
        brand_context={
            "series_name": SERIES_NAME,
            "surface": "instagram_reels",
            "account": "@libertaverdades",
            "publish_style": overrides.get("publish_style") or PUBLISH_STYLE,
            "goal": overrides.get("goal") or mission_decision.get("goal"),
        },
        format_hint=overrides.get("publish_format_now") or mission_decision.get("content_type"),
    )

    plan = _map_soberano_to_creative_plan(
        trend,
        sovereign,
        overrides=overrides,
        mission_decision=mission_decision,
        recent_memory=recent_memory,
    )

    plan.notes.append("planner_path=official_consolidated")
    return plan
