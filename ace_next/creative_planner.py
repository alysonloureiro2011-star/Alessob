from __future__ import annotations

import logging
import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

from .caption_comprehension_gate import evaluate_caption_comprehension
from .creative_planner_soberano_v1 import build_creative_plan_soberano_v1
from .editorial_examples import examples_context
from .editorial_policy import BRAND_PERSONA, POLICY_VERSION, TONE_OF_VOICE, get_editorial_policy, lexicon_hits
from .editorial_rubric import evaluate_editorial_quality
from .serial_continuity_engine import build_serial_continuity


logger = logging.getLogger(__name__)

STOPWORDS = {
    "a", "ao", "aos", "as", "às", "com", "como", "da", "das", "de", "do", "dos", "e", "é",
    "em", "mais", "menos", "na", "nas", "no", "nos", "o", "os", "ou", "para", "por", "que",
    "se", "sem", "sobre", "um", "uma", "uns", "umas",
}

WEAK_INPUTS = {"", "123", "aaa", "hello", "oi", "test", "teste", "teste real"}
SERIES_NAME = "Liberta a Verdade"
VISUAL_STYLE = "visual_foundation_pack_v1"
PUBLISH_STYLE = "official_next_visual_foundation_v1"
STRATEGIC_TARGET_FORMAT = "reel_premium"
PUBLISH_FORMAT_NOW = "image"
VALID_PUBLISH_FORMATS = {"image", "carousel", "story", "reel"}


@dataclass
class CreativePlan:
    trend_input: str
    topic_seed: str
    series_name: str
    objective: str
    strategic_target_format: str
    publish_format_now: str
    angle: str
    hook: str
    headline: str
    body: str
    support_points: list[str]
    caption: str
    first_comment: str
    hashtags: list[str]
    cta: str
    visual_style: str
    color_profile: str
    publish_style: str
    quality_score: int
    notes: list[str]
    policy_version: str
    brand_persona: str
    tone_of_voice: list[str]
    brand_lexicon_hits: list[str]
    approved_example_ids: list[str]
    rejected_example_ids: list[str]
    editorial_score_breakdown: dict[str, Any]
    editorial_reasons: list[str]
    editorial_flags: list[str]
    planner_selected: str
    problem: str | None = None
    insight: str | None = None
    format_recommendation: str | None = None
    hook_family: str | None = None
    narrative_tension: str | None = None
    payoff: str | None = None
    sequel_potential: str | None = None
    risk_flags: list[str] | None = None
    editorial_critic: dict[str, Any] | None = None
    caption_gate: dict[str, Any] | None = None
    caption_gate_result: bool | None = None
    caption_gate_score: float | None = None
    caption_gate_flags: list[str] | None = None
    caption_gate_reasons: list[str] | None = None
    continuation_candidate: bool | None = None
    planner_version: str | None = None
    planner_mode: str | None = None
    deterministic: bool | None = None
    deterministic_path: bool | None = None
    perceived_value_hypothesis: str | None = None
    timing_hypothesis: str | None = None
    serial_continuity: dict[str, Any] | None = None
    distribution_context: dict[str, Any] | None = None
    fallback_flags: list[str] | None = None
    official_path_quality_state: str | None = None
    goal: str | None = None
    hypothesis: str | None = None
    mission_context: dict[str, Any] | None = None
    override_summary: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(char)
    )


def _normalize(value: str) -> str:
    return _strip_accents(_clean_text(value)).lower()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _normalize(value))


def _topic_seed(trend: str) -> str:
    clean = _clean_text(trend)
    if _normalize(clean) in WEAK_INPUTS:
        return "clareza, disciplina e direção"
    return clean or "clareza, disciplina e direção"


def _keywords(topic: str) -> list[str]:
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", topic.lower())
    unique: list[str] = []
    for word in words:
        if len(word) < 3:
            continue
        if word in STOPWORDS:
            continue
        if word not in unique:
            unique.append(word)
    return unique[:8]


def _family(keywords: list[str]) -> str:
    base = {_normalize(word) for word in keywords if _normalize(word)}
    families = {
        "faith": {"fe", "proposito", "deus", "jesus", "biblia", "espiritual", "oracao"},
        "discipline": {"disciplina", "foco", "clareza", "execucao", "consistencia", "direcao", "resultado"},
        "emotion": {"ansiedade", "medo", "mente", "emocional", "emocao", "paz", "controle"},
        "prosperity": {"prosperidade", "riqueza", "financeiro", "financeira", "abundancia", "escassez", "dinheiro"},
        "branding": {"marca", "conteudo", "instagram", "autoridade", "posicionamento", "comunicacao"},
    }
    best_family = "editorial"
    best_hits = 0
    for name, terms in families.items():
        hits = len(base & terms)
        if hits > best_hits:
            best_hits = hits
            best_family = name
    return best_family


def _choose_color_profile(keywords: list[str]) -> str:
    family = _family(keywords)
    if family in {"discipline", "emotion", "branding"}:
        return "electric_blue"
    if family == "prosperity":
        return "amber_gold"
    return "editorial_violet"


def _hashtags(keywords: list[str], family: str) -> list[str]:
    tags = [f"#{_slug(word)}" for word in keywords if _slug(word)]
    family_tags = {
        "faith": ["#proposito", "#conviccao", "#direcao"],
        "emotion": ["#clarezamental", "#controleemocional", "#equilibrio"],
        "prosperity": ["#prosperidade", "#execucao", "#consistencia"],
        "discipline": ["#disciplina", "#foco", "#direcao"],
        "branding": ["#posicionamento", "#autoridade", "#conteudocomcriterio"],
        "editorial": ["#clareza", "#estrategia", "#direcao"],
    }
    tags.extend(family_tags.get(family, []))
    tags.extend(["#libertaaverdade", "#valorreal", "#mentalidade"])
    unique: list[str] = []
    for tag in tags:
        if tag and tag not in unique:
            unique.append(tag)
    return unique[:8]


def _first_comment(topic: str, support_points: list[str], hashtags: list[str]) -> str:
    opening = f"Qual parte disso mais pesa hoje em {topic}?"
    proof = support_points[0] if support_points else "Clareza muda execução."
    return f"{opening} {proof} {' '.join(hashtags[:4])}".strip()


def _compose_caption(hook: str, headline: str, body: str, support_points: list[str], cta: str, hashtags: list[str]) -> str:
    bullets = "\n".join(f"• {point}" for point in support_points[:3])
    return (
        f"{hook}\n\n"
        f"{headline}\n\n"
        f"{body}\n\n"
        f"Pontos de apoio:\n{bullets}\n\n"
        f"{cta}\n\n"
        f"{' '.join(hashtags[:5])}"
    )


def _normalize_publish_format(value: Any, default: str) -> str:
    normalized = _clean_text(str(value or "")).lower()
    if normalized in VALID_PUBLISH_FORMATS:
        return normalized
    return default


def _normalize_text_override(value: Any) -> str | None:
    cleaned = _clean_text(str(value or ""))
    return cleaned or None


def _recommended_next_series_action(serial_continuity: dict[str, Any], recent_memory: list[dict[str, Any]] | None) -> str:
    role = str(serial_continuity.get("episode_role") or "")
    if role == "follow_up":
        return "continuar a série com aprofundamento disciplinado"
    if recent_memory:
        return "ligar o próximo episódio ao contexto recente sem fingir continuidade forte"
    return "abrir continuidade conservadora sem forçar série"


def _apply_overrides_to_plan(
    plan: CreativePlan,
    *,
    overrides: dict[str, Any] | None = None,
    mission_decision: dict[str, Any] | None = None,
) -> CreativePlan:
    overrides = dict(overrides or {})
    mission_decision = dict(mission_decision or {})

    strategic_target_format = _normalize_text_override(overrides.get("strategic_target_format"))
    publish_format_now = _normalize_publish_format(
        overrides.get("publish_format_now"),
        plan.publish_format_now,
    )
    publish_style = _normalize_text_override(overrides.get("publish_style"))
    goal = _normalize_text_override(overrides.get("goal")) or _normalize_text_override(mission_decision.get("goal"))
    hypothesis = _normalize_text_override(overrides.get("hypothesis")) or _normalize_text_override(mission_decision.get("hypothesis"))
    planner_context = _normalize_text_override(overrides.get("planner_selected")) or _normalize_text_override(mission_decision.get("planner_selected"))

    override_summary = {
        "strategic_target_format": strategic_target_format or plan.strategic_target_format,
        "publish_format_now": publish_format_now,
        "publish_style": publish_style or plan.publish_style,
        "goal": goal,
        "hypothesis": hypothesis,
        "planner_context": planner_context,
    }

    if strategic_target_format:
        plan.strategic_target_format = strategic_target_format
        plan.notes.append(f"override_strategic_target_format={strategic_target_format}")

    if publish_format_now != plan.publish_format_now:
        plan.publish_format_now = publish_format_now
        plan.notes.append(f"override_publish_format_now={publish_format_now}")

    if publish_style:
        plan.publish_style = publish_style
        plan.notes.append(f"override_publish_style={publish_style}")

    if goal:
        plan.objective = goal
        plan.goal = goal
        plan.notes.append(f"mission_goal={goal}")
    else:
        plan.goal = plan.objective

    if hypothesis:
        plan.hypothesis = hypothesis
        plan.notes.append(f"mission_hypothesis={hypothesis}")

    if planner_context:
        plan.notes.append(f"mission_planner_context={planner_context}")

    if mission_decision:
        plan.notes.append("mission_decision_wired=true")

    if mission_decision and mission_decision.get("content_type"):
        plan.notes.append(f"mission_content_type={mission_decision.get('content_type')}")

    plan.mission_context = {
        "goal": mission_decision.get("goal"),
        "hypothesis": mission_decision.get("hypothesis"),
        "content_type": mission_decision.get("content_type"),
        "planner_selected": mission_decision.get("planner_selected"),
        "priority": mission_decision.get("priority"),
        "confidence": mission_decision.get("confidence"),
    } if mission_decision else {}

    plan.override_summary = override_summary
    return plan


def _apply_caption_and_continuity(
    plan: CreativePlan,
    *,
    recent_memory: list[dict[str, Any]] | None = None,
) -> CreativePlan:
    recent_memory = list(recent_memory or [])

    caption_gate = evaluate_caption_comprehension(
        headline=plan.headline,
        hook=plan.hook,
        body=plan.body,
        cta=plan.cta,
    )
    plan.caption_gate = caption_gate
    plan.caption_gate_result = bool(caption_gate.get("approved"))
    plan.caption_gate_score = float(caption_gate.get("score") or 0.0)
    plan.caption_gate_flags = list(caption_gate.get("flags") or [])
    plan.caption_gate_reasons = list(caption_gate.get("reasons") or [])

    plan.notes.append(f"caption_gate_result={str(plan.caption_gate_result).lower()}")
    plan.notes.append(f"caption_gate_score={plan.caption_gate_score}")
    if plan.caption_gate_flags:
        plan.notes.append(f"caption_gate_flags={','.join(plan.caption_gate_flags)}")

    fallback_flags = list(plan.fallback_flags or [])
    if not plan.caption_gate_result:
        if "caption_gate_soft_fail" not in fallback_flags:
            fallback_flags.append("caption_gate_soft_fail")
        plan.official_path_quality_state = "caption_gate_soft_fail"
    else:
        if not plan.official_path_quality_state or plan.official_path_quality_state == "conservative_fallback":
            plan.official_path_quality_state = "caption_gate_passed"

    plan.fallback_flags = fallback_flags

    serial_continuity = build_serial_continuity(
        creative_plan=plan.to_dict(),
        recent_memory=recent_memory,
    )
    plan.serial_continuity = serial_continuity
    plan.continuation_candidate = bool(serial_continuity.get("next_episode_seed"))

    existing_distribution = dict(plan.distribution_context or {})
    recommended_next_format = (
        existing_distribution.get("recommended_next_format")
        or serial_continuity.get("linked_format_suggestion")
        or plan.publish_format_now
    )
    recommended_next_angle = (
        existing_distribution.get("recommended_next_angle")
        or serial_continuity.get("next_episode_seed")
        or plan.angle
    )
    recommended_next_series_action = (
        existing_distribution.get("recommended_next_series_action")
        or _recommended_next_series_action(serial_continuity, recent_memory)
    )
    recommended_timing_hypothesis = (
        existing_distribution.get("recommended_timing_hypothesis")
        or plan.timing_hypothesis
        or "24-48h com leitura conservadora do sinal"
    )

    plan.distribution_context = {
        "recommended_next_format": recommended_next_format,
        "recommended_next_angle": recommended_next_angle,
        "recommended_next_series_action": recommended_next_series_action,
        "recommended_timing_hypothesis": recommended_timing_hypothesis,
        "source_mode": "memory_informed" if recent_memory else "conservative_fallback",
    }

    plan.notes.append(f"planner_mode={plan.planner_mode}")
    plan.notes.append(f"deterministic_path={str(bool(plan.deterministic_path)).lower()}")

    return plan


def _map_soberano_to_creative_plan(
    trend: str,
    sovereign: dict[str, Any],
    *,
    overrides: dict[str, Any] | None = None,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
) -> CreativePlan:
    topic_seed = _topic_seed(str(sovereign.get("topic_seed") or trend))
    keywords = _keywords(topic_seed)
    family = _family(keywords)
    hashtags = _hashtags(keywords, family)
    support_points = [str(item) for item in sovereign.get("support_points") or []][:3]
    cta = str(sovereign.get("cta") or "Salve para reler e envie para alguém que precisa disso.")
    hook = str(sovereign.get("hook") or "")
    headline = str(sovereign.get("headline") or "")
    body = str(sovereign.get("body") or "")
    caption = _compose_caption(hook, headline, body, support_points, cta, hashtags)
    first_comment = _first_comment(topic_seed, support_points, hashtags)

    critic = dict(sovereign.get("critic") or sovereign.get("editorial_critic") or {})
    caption_gate = dict(sovereign.get("caption_gate") or critic.get("caption_gate") or {})
    notes = list(sovereign.get("notes") or [])
    notes.append("planner_selected=creative_planner_soberano_v1")

    logger.info("planner_selected=creative_planner_soberano_v1")
    logger.info("planner_generation_ok=true")
    logger.info("caption_gate_result=%s", caption_gate.get("approved"))
    logger.info("editorial_critic_result=%s", critic.get("approved"))

    plan = CreativePlan(
        trend_input=_clean_text(trend),
        topic_seed=topic_seed,
        series_name=str(sovereign.get("series_name") or SERIES_NAME),
        objective=str(sovereign.get("problem") or "reorganizar percepção, direção e execução"),
        strategic_target_format=STRATEGIC_TARGET_FORMAT,
        publish_format_now=_normalize_publish_format(
            sovereign.get("format_recommendation") or PUBLISH_FORMAT_NOW,
            PUBLISH_FORMAT_NOW,
        ),
        angle=str(sovereign.get("angle") or ""),
        hook=hook,
        headline=headline,
        body=body,
        support_points=support_points,
        caption=caption,
        first_comment=first_comment,
        hashtags=hashtags,
        cta=cta,
        visual_style=VISUAL_STYLE,
        color_profile=_choose_color_profile(keywords),
        publish_style=PUBLISH_STYLE,
        quality_score=int(round(float(critic.get("final_score") or 0))),
        notes=notes,
        policy_version=str(get_editorial_policy().get("version") or POLICY_VERSION),
        brand_persona=BRAND_PERSONA,
        tone_of_voice=list(TONE_OF_VOICE),
        brand_lexicon_hits=list(sovereign.get("brand_lexicon_hits") or sovereign.get("brand_fit_signals") or lexicon_hits(caption)),
        approved_example_ids=list(examples_context(topic_seed)["approved_ids"]),
        rejected_example_ids=list(examples_context(topic_seed)["rejected_ids"]),
        editorial_score_breakdown=dict(critic.get("breakdown") or {}),
        editorial_reasons=list(critic.get("rejection_reasons") or ["critic_aprovou_sem_restrições"]),
        editorial_flags=list(caption_gate.get("flags") or []),
        planner_selected="creative_planner_soberano_v1",
        problem=str(sovereign.get("problem") or ""),
        insight=str(sovereign.get("insight") or ""),
        format_recommendation=str(sovereign.get("format_recommendation") or PUBLISH_FORMAT_NOW),
        hook_family=str(sovereign.get("hook_family") or ""),
        narrative_tension=str(sovereign.get("narrative_tension") or ""),
        payoff=str(sovereign.get("payoff") or ""),
        sequel_potential=str(sovereign.get("sequel_potential") or "medium"),
        risk_flags=list(sovereign.get("fallback_flags") or []),
        editorial_critic=critic,
        caption_gate=caption_gate,
        continuation_candidate=bool(sovereign.get("continuation_candidate")),
        planner_version=str(sovereign.get("planner_version") or "editorial_soberano_v1"),
        planner_mode=str(sovereign.get("planner_mode") or "deterministic"),
        deterministic=bool(sovereign.get("deterministic")),
        deterministic_path=bool(sovereign.get("deterministic_path")),
        perceived_value_hypothesis=str(sovereign.get("perceived_value_hypothesis") or ""),
        timing_hypothesis=str(sovereign.get("timing_hypothesis") or ""),
        serial_continuity=dict(sovereign.get("serial_continuity") or {}),
        distribution_context=dict(sovereign.get("distribution_context") or {}),
        fallback_flags=list(sovereign.get("fallback_flags") or []),
        official_path_quality_state=str(sovereign.get("official_path_quality_state") or "conservative_fallback"),
        goal=str(sovereign.get("goal") or ""),
        hypothesis=str(sovereign.get("hypothesis") or ""),
        mission_context={},
        override_summary={},
    )
    plan = _apply_overrides_to_plan(plan, overrides=overrides, mission_decision=mission_decision)
    return _apply_caption_and_continuity(plan, recent_memory=recent_memory)


def _build_creative_plan_legacy(
    trend: str,
    *,
    overrides: dict[str, Any] | None = None,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
) -> CreativePlan:
    policy = get_editorial_policy()
    clean_input = _clean_text(trend)
    topic = _topic_seed(clean_input)
    keywords = _keywords(topic)
    hashtags = _hashtags(keywords, _family(keywords))

    headline = "Sem disciplina, clareza perde força antes de virar resultado."
    hook = "O problema raramente é falta de esforço. Quase sempre é mover muito sem critério suficiente."
    body = "Quando estrutura entra, intenção deixa de depender do humor do dia. E quando o eixo volta ao lugar, o resultado começa a responder a processo, não a impulso."
    support_points = [
        "Clareza sem estrutura não sustenta consistência.",
        "Disciplina organiza prioridade antes da pressa.",
        "Direção reduz ruído e melhora execução.",
    ]
    cta = "Salve para revisar antes da próxima decisão e envie para alguém que precisa de mais critério."
    caption = _compose_caption(hook, headline, body, support_points, cta, hashtags)
    first_comment = _first_comment(topic, support_points, hashtags)

    editorial_qa = evaluate_editorial_quality(
        {
            "trend_input": clean_input,
            "topic_seed": topic,
            "headline": headline,
            "hook": hook,
            "body": body,
            "support_points": support_points,
            "cta": cta,
            "hashtags": hashtags,
        }
    )

    notes = [
        f"policy={POLICY_VERSION}",
        "planner_mode=legacy_fallback",
        "planner_selected=creative_planner_legacy",
    ]

    logger.info("planner_selected=creative_planner_legacy")
    logger.info("planner_generation_ok=legacy")

    plan = CreativePlan(
        trend_input=clean_input,
        topic_seed=topic,
        series_name=SERIES_NAME,
        objective="entregar uma peça editorial clara e útil",
        strategic_target_format=STRATEGIC_TARGET_FORMAT,
        publish_format_now=PUBLISH_FORMAT_NOW,
        angle="transformar intenção em critério e direção",
        hook=hook,
        headline=headline,
        body=body,
        support_points=support_points,
        caption=caption,
        first_comment=first_comment,
        hashtags=hashtags,
        cta=cta,
        visual_style=VISUAL_STYLE,
        color_profile=_choose_color_profile(keywords),
        publish_style=PUBLISH_STYLE,
        quality_score=editorial_qa.final_score,
        notes=notes,
        policy_version=policy["version"],
        brand_persona=BRAND_PERSONA,
        tone_of_voice=list(TONE_OF_VOICE),
        brand_lexicon_hits=lexicon_hits(" ".join([headline, hook, body, cta] + support_points)),
        approved_example_ids=list(examples_context(topic)["approved_ids"]),
        rejected_example_ids=list(examples_context(topic)["rejected_ids"]),
        editorial_score_breakdown=dict(editorial_qa.breakdown),
        editorial_reasons=list(editorial_qa.reasons),
        editorial_flags=list(editorial_qa.flags),
        planner_selected="creative_planner_legacy",
        planner_version="legacy_fallback",
        planner_mode="legacy_fallback",
        deterministic=True,
        deterministic_path=True,
        continuation_candidate=False,
        serial_continuity={},
        distribution_context={},
        fallback_flags=["legacy_fallback"],
        official_path_quality_state="conservative_fallback",
        goal=None,
        hypothesis=None,
        mission_context={},
        override_summary={},
    )
    plan = _apply_overrides_to_plan(plan, overrides=overrides, mission_decision=mission_decision)
    return _apply_caption_and_continuity(plan, recent_memory=recent_memory)


def build_creative_plan(
    trend: str,
    overrides: dict[str, Any] | None = None,
    mission_decision: dict[str, Any] | None = None,
    recent_memory: list[dict[str, Any]] | None = None,
) -> CreativePlan:
    overrides = dict(overrides or {})
    mission_decision = dict(mission_decision or {})
    format_hint = (
        overrides.get("publish_format_now")
        or mission_decision.get("content_type")
        or None
    )

    try:
        sovereign = build_creative_plan_soberano_v1(
            topic_seed=trend,
            signal_context=None,
            brand_context=None,
            format_hint=format_hint,
        )
        return _map_soberano_to_creative_plan(
            trend,
            sovereign,
            overrides=overrides,
            mission_decision=mission_decision,
            recent_memory=recent_memory,
        )
    except Exception as exc:
        logger.exception("planner_generation_fail")
        legacy = _build_creative_plan_legacy(
            trend,
            overrides=overrides,
            mission_decision=mission_decision,
            recent_memory=recent_memory,
        )
        legacy.notes.append(f"planner_generation_fail=creative_planner_soberano_v1:{type(exc).__name__}")
        legacy.notes.append("planner_selected=creative_planner_legacy_after_soberano_fail")
        return legacy
