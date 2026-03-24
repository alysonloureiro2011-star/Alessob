from __future__ import annotations

from typing import Any

from .brand_lexicon import get_brand_lexicon, normalize_text, scan_brand_alignment
from .caption_comprehension_gate import evaluate_caption_comprehension


def _bounded(value: float) -> float:
    return max(0.0, min(round(value, 2), 10.0))


def evaluate_editorial_critic(plan: dict[str, Any], lexicon: dict | None = None) -> dict[str, Any]:
    lexicon = lexicon or get_brand_lexicon()

    headline = str(plan.get("headline") or "").strip()
    hook = str(plan.get("hook") or "").strip()
    body = str(plan.get("body") or "").strip()
    cta = str(plan.get("cta") or "").strip()
    payoff = str(plan.get("payoff") or "").strip()
    narrative_tension_text = str(plan.get("narrative_tension") or "").strip()

    gate = evaluate_caption_comprehension(headline, hook, body, cta, lexicon)
    alignment = scan_brand_alignment(" ".join([headline, hook, body, cta, payoff, narrative_tension_text]), lexicon)

    hook_strength = 5.5
    if len(normalize_text(hook)) >= 95:
        hook_strength += 1.2
    if any(term in normalize_text(hook) for term in ["quase sempre", "o problema", "raramente", "custo", "erro"]):
        hook_strength += 1.4
    if alignment["tension_anchors"]:
        hook_strength += 1.0
    hook_strength = _bounded(hook_strength)

    headline_strength = 5.5
    if len(normalize_text(headline)) >= 32:
        headline_strength += 1.2
    if "." in headline or ":" not in headline:
        headline_strength += 0.8
    if any(term in normalize_text(headline) for term in ["sem ", "perde forca", "vira", "custa"]):
        headline_strength += 1.2
    headline_strength = _bounded(headline_strength)

    perceived_value = 5.2
    perceived_value += min(len(alignment["perceived_value_anchors"]) * 1.0, 2.0)
    if len(normalize_text(body).split()) >= 28:
        perceived_value += 1.0
    if payoff:
        perceived_value += 1.0
    perceived_value = _bounded(perceived_value)

    narrative_tension = 5.0
    if alignment["tension_anchors"]:
        narrative_tension += 1.5
    if narrative_tension_text:
        narrative_tension += 1.0
    if any(term in normalize_text(hook + " " + body) for term in ["travamento", "ruido", "desgaste", "custo", "erro"]):
        narrative_tension += 1.2
    narrative_tension = _bounded(narrative_tension)

    semantic_density = _bounded(gate["breakdown"]["semantic_density"] + 0.4)
    clarity = _bounded(gate["breakdown"]["clarity"])
    naturality = _bounded(gate["breakdown"]["naturality"])
    anti_genericity = _bounded(gate["breakdown"]["anti_generic"])
    anti_commodity = _bounded(gate["breakdown"]["anti_commodity"])

    brand_fit = 5.8
    brand_fit += min(len(alignment["semantic_anchors"]) * 0.45, 1.8)
    brand_fit += min(len(alignment["approved_language_patterns"]) * 0.6, 1.2)
    if not alignment["disallowed_patterns"]:
        brand_fit += 1.0
    if not any(term in normalize_text(headline + " " + hook) for term in ["viral", "segredo", "antes que seja tarde"]):
        brand_fit += 0.8
    brand_fit = _bounded(brand_fit)

    breakdown = {
        "brand_fit": brand_fit,
        "anti_genericity": anti_genericity,
        "anti_commodity": anti_commodity,
        "naturality": naturality,
        "hook_strength": hook_strength,
        "headline_strength": headline_strength,
        "clarity": clarity,
        "perceived_value": perceived_value,
        "semantic_density": semantic_density,
        "narrative_tension": narrative_tension,
    }

    failed_floors: list[str] = []
    floor_map = {
        "brand_fit": 8.5,
        "anti_genericity": 8.0,
        "anti_commodity": 8.0,
        "naturality": 7.5,
        "hook_strength": 7.5,
        "headline_strength": 7.5,
        "clarity": 8.0,
        "perceived_value": 7.5,
        "semantic_density": 7.5,
        "narrative_tension": 7.0,
    }
    for key, floor in floor_map.items():
        if breakdown[key] < floor:
            failed_floors.append(key)

    rejection_reasons = list(gate.get("reasons") or [])
    if "narrative_tension" in failed_floors:
        rejection_reasons.append("a tensão narrativa ainda não sustenta retenção premium")
    if "perceived_value" in failed_floors:
        rejection_reasons.append("o valor percebido ainda não está forte o suficiente")
    if "brand_fit" in failed_floors:
        rejection_reasons.append("a peça ainda não sustenta padrão de marca soberano")

    rewrite_recommendations: list[str] = []
    if "hook_strength" in failed_floors:
        rewrite_recommendations.append("fortalecer hook com custo oculto, erro comum ou contraste de leitura")
    if "headline_strength" in failed_floors:
        rewrite_recommendations.append("encurtar headline e aumentar precisão causal")
    if "anti_genericity" in failed_floors:
        rewrite_recommendations.append("trocar abstração por semântica concreta ancorada no léxico da marca")
    if "anti_commodity" in failed_floors:
        rewrite_recommendations.append("remover promessas commodity e CTA apelativo")
    if "narrative_tension" in failed_floors:
        rewrite_recommendations.append("inserir fricção real antes do payoff")

    final_score = round((sum(breakdown.values()) / len(breakdown)) * 10, 2)
    approved = len(failed_floors) == 0 and gate.get("approved", False)

    return {
        "ok": True,
        "approved": approved,
        "final_score": final_score,
        "breakdown": breakdown,
        "failed_floors": failed_floors,
        "rejection_reasons": rejection_reasons,
        "rewrite_recommendations": rewrite_recommendations,
        "brand_fit": brand_fit,
        "anti_genericity": anti_genericity,
        "anti_commodity": anti_commodity,
        "naturality": naturality,
        "hook_strength": hook_strength,
        "headline_strength": headline_strength,
        "clarity": clarity,
        "perceived_value": perceived_value,
        "semantic_density": semantic_density,
        "narrative_tension": narrative_tension,
        "caption_gate": gate,
    }


def editorial_critic_examples() -> dict[str, Any]:
    approved_plan = {
        "headline": "Sem disciplina, clareza perde força antes de virar resultado.",
        "hook": "O problema raramente é falta de esforço. Quase sempre é mover muito sem critério suficiente.",
        "body": "Quando estrutura entra, a intenção deixa de depender do humor do dia. E quando o eixo volta ao lugar, o resultado começa a responder a processo, não a impulso.",
        "cta": "Salve para revisar antes da próxima decisão e envie para alguém que precisa de mais critério e menos ruído.",
        "payoff": "execução ganha forma e direção",
        "narrative_tension": "boa intenção sem eixo se dispersa",
    }
    rejected_plan = {
        "headline": "Acredite em você e tudo vai mudar",
        "hook": "Descubra o segredo que ninguém te conta",
        "body": "Sua vida pode mudar agora.",
        "cta": "Comente aqui",
        "payoff": "",
        "narrative_tension": "",
    }
    return {
        "ok": True,
        "approved_example": evaluate_editorial_critic(approved_plan),
        "rejected_example": evaluate_editorial_critic(rejected_plan),
    }
