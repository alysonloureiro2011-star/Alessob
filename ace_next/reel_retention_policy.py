from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class RetentionPolicyResult:
    hook_opening_strength: float
    pattern_interrupt_density: float
    curiosity_gap_strength: float
    payoff_clarity: float
    cta_strength: float
    naturalism_score: float
    cinematic_score: float
    algorithmic_priority_score: float
    premium_eligibility_score: float
    publish_ready: bool
    veto_reasons: list[str]
    lift_targets: list[str]
    study_axes_applied: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


STUDY_AXES = [
    "hook_opening_0_3s",
    "pattern_interrupt_3_5s",
    "micro_payoffs",
    "curiosity_gap",
    "cta_strength",
    "naturalismo_real_v2",
    "cinematic_authority",
    "algorithmic_priority_watchtime_shares_saves_completion",
]


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _score_presence(text: str, threshold: int, full: float = 10.0) -> float:
    length = len(_safe_text(text))
    if length <= 0:
        return 0.0
    if length >= threshold:
        return full
    return round((length / threshold) * full, 2)


def _score_hook(hook: str, headline: str) -> float:
    base = _score_presence(hook, 90)
    if any(token in hook.lower() for token in ["por que", "ninguém", "erro", "verdade", "pare", "antes"]):
        base += 1.0
    if headline and len(headline) >= 18:
        base += 0.5
    return min(round(base, 2), 10.0)


def _score_pattern_interrupt(notes: list[str], support_points: list[str]) -> float:
    hits = 0
    joined_notes = " ".join(notes).lower()
    if any(token in joined_notes for token in ["pattern", "interrupt", "rhythm", "cadencia", "corte"]):
        hits += 2
    hits += min(len([p for p in support_points if _safe_text(p)]), 3)
    return min(float(hits * 2), 10.0)


def _score_curiosity_gap(hook: str, headline: str, angle: str) -> float:
    text = " ".join([hook, headline, angle]).lower()
    score = 0.0
    if any(token in text for token in ["por que", "o que", "como", "antes", "ninguém", "verdade"]):
        score += 5.0
    if any(token in text for token in ["erro", "segredo", "padrão", "ilusão", "armadilha"]):
        score += 3.0
    if len(text) > 60:
        score += 1.5
    return min(round(score, 2), 10.0)


def _score_payoff(body: str, support_points: list[str]) -> float:
    score = _score_presence(body, 180)
    if len([p for p in support_points if _safe_text(p)]) >= 2:
        score += 1.5
    return min(round(score, 2), 10.0)


def _score_cta(cta: str) -> float:
    text = cta.lower()
    score = _score_presence(cta, 60)
    if any(token in text for token in ["salve", "envie", "compartilhe", "comente"]):
        score += 2.0
    return min(round(score, 2), 10.0)


def _score_naturalism(visual_style: str, publish_style: str, notes: list[str]) -> float:
    text = " ".join([visual_style, publish_style, " ".join(notes)]).lower()
    score = 3.0
    if any(token in text for token in ["natural", "organic", "micro", "human", "real"]):
        score += 3.0
    if any(token in text for token in ["grain", "cinematic", "texture", "breath", "express"]):
        score += 2.0
    return min(round(score, 2), 10.0)


def _score_cinematic(color_profile: str, visual_style: str, publish_style: str) -> float:
    text = " ".join([color_profile, visual_style, publish_style]).lower()
    score = 3.0
    if any(token in text for token in ["cinematic", "premium", "authority", "editorial"]):
        score += 3.0
    if any(token in text for token in ["color", "frame", "16:9", "9:16", "bokeh"]):
        score += 2.0
    return min(round(score, 2), 10.0)


def _score_algorithmic_priority(format_now: str, strategic_target_format: str, cta: str) -> float:
    score = 2.0
    if format_now in {"reel", "carousel"}:
        score += 3.0
    if "reel" in _safe_text(strategic_target_format).lower():
        score += 2.0
    if any(token in cta.lower() for token in ["salve", "envie", "compartilhe"]):
        score += 2.0
    return min(round(score, 2), 10.0)


def evaluate_reel_retention_policy(creative_plan: dict[str, Any]) -> dict[str, Any]:
    plan = dict(creative_plan or {})
    hook = _safe_text(plan.get("hook"))
    headline = _safe_text(plan.get("headline"))
    angle = _safe_text(plan.get("angle"))
    body = _safe_text(plan.get("body"))
    cta = _safe_text(plan.get("cta"))
    support_points = [str(item) for item in plan.get("support_points") or []]
    notes = [str(item) for item in plan.get("notes") or []]
    visual_style = _safe_text(plan.get("visual_style"))
    publish_style = _safe_text(plan.get("publish_style"))
    color_profile = _safe_text(plan.get("color_profile"))
    format_now = _safe_text(plan.get("publish_format_now")).lower()
    strategic_target_format = _safe_text(plan.get("strategic_target_format")).lower()

    hook_opening_strength = _score_hook(hook, headline)
    pattern_interrupt_density = _score_pattern_interrupt(notes, support_points)
    curiosity_gap_strength = _score_curiosity_gap(hook, headline, angle)
    payoff_clarity = _score_payoff(body, support_points)
    cta_strength = _score_cta(cta)
    naturalism_score = _score_naturalism(visual_style, publish_style, notes)
    cinematic_score = _score_cinematic(color_profile, visual_style, publish_style)
    algorithmic_priority_score = _score_algorithmic_priority(format_now, strategic_target_format, cta)

    premium_eligibility_score = round(
        (
            hook_opening_strength * 0.2
            + pattern_interrupt_density * 0.1
            + curiosity_gap_strength * 0.15
            + payoff_clarity * 0.1
            + cta_strength * 0.1
            + naturalism_score * 0.15
            + cinematic_score * 0.1
            + algorithmic_priority_score * 0.1
        ),
        2,
    )

    veto_reasons: list[str] = []
    lift_targets: list[str] = []

    if hook_opening_strength < 6.5:
        veto_reasons.append("hook_opening_fraco")
        lift_targets.append("reforcar_hook_0_3s")
    if curiosity_gap_strength < 6.0:
        veto_reasons.append("curiosity_gap_fraco")
        lift_targets.append("elevar_curiosity_gap")
    if cta_strength < 5.5:
        lift_targets.append("fortalecer_cta_salvar_compartilhar")
    if naturalism_score < 6.5:
        veto_reasons.append("naturalismo_abaixo_do_minimo")
        lift_targets.append("reduzir_ia_vibe_e_elevar_textura_organica")
    if cinematic_score < 6.0:
        lift_targets.append("elevar_autoridade_visual_cinematografica")
    if algorithmic_priority_score < 6.0:
        lift_targets.append("aproximar_formato_de_distribuicao_prioritaria")

    publish_ready = premium_eligibility_score >= 7.2 and len(veto_reasons) == 0

    result = RetentionPolicyResult(
        hook_opening_strength=hook_opening_strength,
        pattern_interrupt_density=pattern_interrupt_density,
        curiosity_gap_strength=curiosity_gap_strength,
        payoff_clarity=payoff_clarity,
        cta_strength=cta_strength,
        naturalism_score=naturalism_score,
        cinematic_score=cinematic_score,
        algorithmic_priority_score=algorithmic_priority_score,
        premium_eligibility_score=premium_eligibility_score,
        publish_ready=publish_ready,
        veto_reasons=veto_reasons,
        lift_targets=lift_targets,
        study_axes_applied=list(STUDY_AXES),
    )
    return result.to_dict()
