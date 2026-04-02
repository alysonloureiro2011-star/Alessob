from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .editorial_staging_hardener import FORMAT_BUDGETS


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
    return " ".join(str(value or "").strip().split())


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _normalize_format(value: Any) -> str:
    normalized = _safe_text(value).lower()
    if normalized in {"story", "stories"}:
        return "story"
    if normalized in {"carousel", "image"}:
        return normalized
    return "image"


def _score_presence(text: str, threshold: int, full: float = 10.0) -> float:
    length = len(_safe_text(text))
    if length <= 0:
        return 0.0
    if length >= threshold:
        return full
    return round((length / threshold) * full, 2)


def _budget_alignment_score(text: str, *, ideal_max: int, hard_max: int, min_chars: int) -> float:
    length = len(_safe_text(text))
    if length == 0:
        return 0.0
    if length < min_chars:
        return 5.8
    if length <= ideal_max:
        return 9.2
    if length <= hard_max:
        overflow = max(1, hard_max - ideal_max)
        penalty = ((length - ideal_max) / overflow) * 2.2
        return max(5.8, round(9.2 - penalty, 2))
    return 4.9


def _contains_any(text: str, tokens: list[str]) -> bool:
    lowered = _safe_text(text).lower()
    return any(token in lowered for token in tokens)


def _score_hook(hook: str, headline: str, fmt: str) -> float:
    hook_budget = FORMAT_BUDGETS[fmt]["hook_chars"]
    hook_presence = _score_presence(hook, 36)
    hook_budget_fit = _budget_alignment_score(
        hook,
        ideal_max=max(36, hook_budget - 14),
        hard_max=hook_budget,
        min_chars=24,
    )

    score = (hook_presence * 0.45) + (hook_budget_fit * 0.55)

    if _contains_any(hook, ["por que", "como", "o que", "antes", "verdade", "erro", "armadilha"]):
        score += 0.8
    if headline and len(_safe_text(headline)) >= 18:
        score += 0.4

    return min(round(score, 2), 10.0)


def _score_pattern_interrupt(notes: list[str], support_points: list[str], fmt: str) -> float:
    hits = 0
    joined_notes = " ".join([_safe_text(item) for item in notes]).lower()

    if _contains_any(joined_notes, ["pattern", "interrupt", "rhythm", "cadencia", "corte", "micro_payoff"]):
        hits += 2

    visible_points = len([p for p in support_points if _safe_text(p)])
    support_limit = FORMAT_BUDGETS[fmt]["support_points_max"]
    if visible_points <= support_limit:
        hits += min(visible_points, 2)
    else:
        hits += 1

    return min(float(hits * 2.2), 10.0)


def _score_curiosity_gap(hook: str, headline: str, angle: str) -> float:
    text = " ".join([hook, headline, angle]).lower()
    score = 0.0

    if _contains_any(text, ["por que", "o que", "como", "antes", "ninguém", "ninguem", "verdade"]):
        score += 5.0
    if _contains_any(text, ["erro", "padrão", "padrao", "ilusão", "ilusao", "armadilha", "quase sempre", "na prática", "na pratica"]):
        score += 3.0
    if len(text) > 50:
        score += 1.2

    return min(round(score, 2), 10.0)


def _score_payoff(body: str, support_points: list[str], fmt: str) -> float:
    body_budget = FORMAT_BUDGETS[fmt]["body_chars"]
    body_fit = _budget_alignment_score(
        body,
        ideal_max=max(54, body_budget - 18),
        hard_max=body_budget,
        min_chars=42,
    )

    support_limit = FORMAT_BUDGETS[fmt]["support_points_max"]
    visible_points = len([p for p in support_points if _safe_text(p)])
    support_bonus = 1.0 if 1 <= visible_points <= support_limit else 0.4

    return min(round(body_fit + support_bonus, 2), 10.0)


def _score_cta(cta: str, fmt: str) -> float:
    cta_budget = FORMAT_BUDGETS[fmt]["cta_chars"]
    score = _budget_alignment_score(
        cta,
        ideal_max=max(18, cta_budget - 8),
        hard_max=cta_budget,
        min_chars=10,
    )

    lowered = _safe_text(cta).lower()

    if _contains_any(lowered, ["salve", "envie", "compartilhe", "releia", "guarde"]):
        score += 1.0

    if _contains_any(lowered, ["comente aqui", "corre", "chama na dm", "compra agora", "agora"]):
        score -= 1.5

    return max(0.0, min(round(score, 2), 10.0))


def _score_naturalism(visual_style: str, publish_style: str, notes: list[str], cta: str) -> float:
    text = " ".join([visual_style, publish_style, " ".join([_safe_text(item) for item in notes]), cta]).lower()
    score = 3.4

    if _contains_any(text, ["natural", "organic", "micro", "human", "real", "grain", "breath", "texture"]):
        score += 3.2

    if not _contains_any(text, ["comente aqui", "corre", "compra agora", "isso muda tudo", "ninguém te conta", "ninguem te conta"]):
        score += 2.0

    return min(round(score, 2), 10.0)


def _score_cinematic(color_profile: str, visual_style: str, publish_style: str) -> float:
    text = " ".join([color_profile, visual_style, publish_style]).lower()
    score = 3.5

    if _contains_any(text, ["cinematic", "premium", "authority", "editorial"]):
        score += 3.0
    if _contains_any(text, ["color", "frame", "9:16", "bokeh", "foley", "ducking"]):
        score += 2.0

    return min(round(score, 2), 10.0)


def _score_algorithmic_priority(format_now: str, strategic_target_format: str, cta: str) -> float:
    score = 2.5

    if format_now in {"reel", "carousel", "image"}:
        score += 2.0
    if any(token in _safe_text(strategic_target_format).lower() for token in ["reel", "carousel", "image", "story"]):
        score += 2.0
    if _contains_any(cta.lower(), ["salve", "envie", "compartilhe", "releia"]):
        score += 2.0

    return min(round(score, 2), 10.0)


def evaluate_reel_retention_policy(creative_plan: dict[str, Any]) -> dict[str, Any]:
    plan = dict(creative_plan or {})

    hook = _safe_text(plan.get("hook"))
    headline = _safe_text(plan.get("headline"))
    angle = _safe_text(plan.get("angle"))
    body = _safe_text(plan.get("body"))
    cta = _safe_text(plan.get("cta"))
    support_points = [str(item) for item in _safe_list(plan.get("support_points"))]
    notes = [str(item) for item in _safe_list(plan.get("notes"))]
    visual_style = _safe_text(plan.get("visual_style"))
    publish_style = _safe_text(plan.get("publish_style"))
    color_profile = _safe_text(plan.get("color_profile"))

    format_now = _normalize_format(plan.get("publish_format_now"))
    strategic_target_format = _normalize_format(plan.get("strategic_target_format"))

    budgets = FORMAT_BUDGETS[format_now]

    hook_opening_strength = _score_hook(hook, headline, format_now)
    pattern_interrupt_density = _score_pattern_interrupt(notes, support_points, format_now)
    curiosity_gap_strength = _score_curiosity_gap(hook, headline, angle)
    payoff_clarity = _score_payoff(body, support_points, format_now)
    cta_strength = _score_cta(cta, format_now)
    naturalism_score = _score_naturalism(visual_style, publish_style, notes, cta)
    cinematic_score = _score_cinematic(color_profile, visual_style, publish_style)
    algorithmic_priority_score = _score_algorithmic_priority(format_now, strategic_target_format, cta)

    premium_eligibility_score = round(
        (
            hook_opening_strength * 0.20
            + pattern_interrupt_density * 0.10
            + curiosity_gap_strength * 0.15
            + payoff_clarity * 0.15
            + cta_strength * 0.10
            + naturalism_score * 0.12
            + cinematic_score * 0.10
            + algorithmic_priority_score * 0.08
        ),
        2,
    )

    veto_reasons: list[str] = []
    lift_targets: list[str] = []

    if len(hook) > budgets["hook_chars"]:
        veto_reasons.append("hook_acima_do_budget_visual")
        lift_targets.append("encurtar_hook_sem_perder_tensao")
    if len(body) > budgets["body_chars"]:
        veto_reasons.append("body_acima_do_budget_visual")
        lift_targets.append("condensar_payoff_sem_perder_valor")
    if len(cta) > budgets["cta_chars"]:
        veto_reasons.append("cta_acima_do_budget_visual")
        lift_targets.append("encurtar_cta_sem_vulgarizar")
    if len([p for p in support_points if _safe_text(p)]) > budgets["support_points_max"]:
        veto_reasons.append("support_points_em_excesso")
        lift_targets.append("reduzir_pontos_visiveis")
    if hook_opening_strength < 6.8:
        veto_reasons.append("hook_opening_fraco")
        lift_targets.append("reforcar_hook_0_3s")
    if curiosity_gap_strength < 6.2:
        veto_reasons.append("curiosity_gap_fraco")
        lift_targets.append("elevar_curiosity_gap")
    if cta_strength < 6.0:
        lift_targets.append("fortalecer_cta_salvar_compartilhar")
    if naturalism_score < 6.8:
        veto_reasons.append("naturalismo_abaixo_do_minimo")
        lift_targets.append("reduzir_ia_vibe_e_elevar_textura_organica")
    if cinematic_score < 6.2:
        lift_targets.append("elevar_autoridade_visual_cinematografica")
    if algorithmic_priority_score < 6.0:
        lift_targets.append("aproximar_formato_da_distribuicao_prioritaria")
    if _contains_any(cta.lower(), ["comente aqui", "corre", "chama na dm", "compra agora"]):
        veto_reasons.append("cta_vulgar_ou_pedinte")
        lift_targets.append("substituir_cta_por_orientacao_soberana")
    if _contains_any(" ".join([headline, hook, body]).lower(), ["segredo", "ninguém te conta", "ninguem te conta", "isso muda tudo", "mude sua vida"]):
        veto_reasons.append("texto_com_traço_commodity")
        lift_targets.append("elevar_angulo_e_remover_cliche")

    publish_ready = premium_eligibility_score >= 7.8 and len(veto_reasons) == 0

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
