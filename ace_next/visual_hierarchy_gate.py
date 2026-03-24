from __future__ import annotations

from typing import Any

from .visual_foundation_soberana_v1 import build_visual_foundation_soberana_v1


def _bounded(value: float) -> float:
    return max(0.0, min(round(value, 2), 10.0))


def evaluate_visual_hierarchy_gate(contract: dict[str, Any]) -> dict[str, Any]:
    contract = dict(contract or {})
    brand_system = dict(contract.get("brand_system") or {})
    template_spec = dict(contract.get("template_spec") or {})
    layout_payload = dict(contract.get("layout_payload") or {})
    gate_payload = dict(contract.get("gate_payload") or {})
    display_payload = dict(layout_payload.get("display_payload") or {})
    computed_lines = dict(gate_payload.get("computed_line_estimates") or {})
    line_expectations = dict(gate_payload.get("line_expectations") or {})
    thresholds = dict(gate_payload.get("minimum_scores") or {})

    failed_floors: list[str] = []
    rejection_reasons: list[str] = []
    recommendations: list[str] = []

    anti_generic_rules = list((brand_system.get("brand_dignity_constraints") or {}).get("anti_generic_identity_rules") or [])
    template_id = str(template_spec.get("template_id") or "")

    headline_lines = int(computed_lines.get("headline_lines") or 0)
    hook_lines = int(computed_lines.get("hook_lines") or 0)
    body_lines = int(computed_lines.get("body_lines") or 0)
    cta_lines = int(computed_lines.get("cta_lines") or 0)
    support_points_count = len(display_payload.get("support_points") or [])

    brand_dignity_score = 5.8
    if "premium" in template_id:
        brand_dignity_score += 1.1
    if anti_generic_rules:
        brand_dignity_score += 1.0
    if "template barato" not in " ".join(anti_generic_rules).lower():
        brand_dignity_score += 0.4
    if headline_lines <= 3 and hook_lines <= 2:
        brand_dignity_score += 0.7
    brand_dignity_score = _bounded(brand_dignity_score)

    contrast_score = 7.8
    if brand_system.get("text_contrast_policy"):
        contrast_score += 0.6
    if display_payload.get("headline") and display_payload.get("hook"):
        contrast_score += 0.3
    contrast_score = _bounded(contrast_score)

    composition_score = 5.8
    if template_spec.get("block_order"):
        composition_score += 1.0
    if headline_lines <= 3:
        composition_score += 1.0
    if body_lines <= 3:
        composition_score += 1.0
    if support_points_count <= 2:
        composition_score += 0.7
    composition_score = _bounded(composition_score)

    legibility_score = 5.8
    if headline_lines <= int(line_expectations.get("headline_lines", 3)):
        legibility_score += 1.2
    if hook_lines <= int(line_expectations.get("hook_lines", 2)):
        legibility_score += 1.1
    if body_lines <= int(line_expectations.get("body_lines", 3)):
        legibility_score += 1.0
    if cta_lines <= int(line_expectations.get("cta_lines", 1)):
        legibility_score += 0.8
    legibility_score = _bounded(legibility_score)

    hierarchy_score = 5.8
    if template_spec.get("block_order") == ["eyebrow", "headline", "hook", "body", "support", "cta"]:
        hierarchy_score += 1.2
    elif template_spec.get("block_order"):
        hierarchy_score += 0.9
    if display_payload.get("headline") and display_payload.get("cta"):
        hierarchy_score += 0.8
    if headline_lines <= 3 and cta_lines <= 1:
        hierarchy_score += 1.0
    hierarchy_score = _bounded(hierarchy_score)

    noise_control_score = 5.6
    if support_points_count <= 2:
        noise_control_score += 1.4
    if body_lines <= 3:
        noise_control_score += 1.0
    if cta_lines <= 1:
        noise_control_score += 1.0
    if headline_lines <= 3 and hook_lines <= 2:
        noise_control_score += 0.8
    noise_control_score = _bounded(noise_control_score)

    breakdown = {
        "brand_dignity_score": brand_dignity_score,
        "contrast_score": contrast_score,
        "composition_score": composition_score,
        "legibility_score": legibility_score,
        "hierarchy_score": hierarchy_score,
        "noise_control_score": noise_control_score,
    }

    for key, minimum in thresholds.items():
        if breakdown.get(key, 0) < float(minimum):
            failed_floors.append(key)

    if headline_lines > int(line_expectations.get("headline_lines", 3)):
        rejection_reasons.append("headline excedeu o line budget")
        recommendations.append("encurtar headline e remover pressão tipográfica")

    if hook_lines > int(line_expectations.get("hook_lines", 2)):
        rejection_reasons.append("hook excedeu o line budget")
        recommendations.append("reduzir hook para contraste curto e mais claro")

    if body_lines > int(line_expectations.get("body_lines", 3)):
        rejection_reasons.append("body excedeu o line budget")
        recommendations.append("cortar explicação excessiva e preservar só a espinha semântica")

    if cta_lines > int(line_expectations.get("cta_lines", 1)):
        rejection_reasons.append("CTA longo demais para peça premium")
        recommendations.append("mover densidade para legenda e manter CTA curto dentro da peça")

    if support_points_count > 2:
        rejection_reasons.append("support points em excesso")
        recommendations.append("manter no máximo dois supports visíveis")

    if brand_dignity_score < thresholds.get("brand_dignity_score", 8.0):
        rejection_reasons.append("a peça ainda não sustenta dignidade visual soberana")
        recommendations.append("reduzir aparência de template e reforçar identidade premium")

    approved = len(failed_floors) == 0 and len(rejection_reasons) == 0
    final_score = round((sum(breakdown.values()) / len(breakdown)) * 10, 2)

    if approved and not rejection_reasons:
        rejection_reasons.append("visual dentro do piso soberano para fundação premium")

    return {
        "ok": True,
        "approved": approved,
        "final_score": final_score,
        "breakdown": breakdown,
        "failed_floors": failed_floors,
        "rejection_reasons": rejection_reasons,
        "recommendations": recommendations,
        "brand_dignity_score": brand_dignity_score,
        "contrast_score": contrast_score,
        "composition_score": composition_score,
        "legibility_score": legibility_score,
        "hierarchy_score": hierarchy_score,
        "noise_control_score": noise_control_score,
        "metrics": {
            "headline_lines": headline_lines,
            "hook_lines": hook_lines,
            "body_lines": body_lines,
            "cta_lines": cta_lines,
            "support_points_count": support_points_count,
            "template_id": template_id,
        },
    }


def visual_hierarchy_gate_examples() -> dict[str, Any]:
    approved_payload = build_visual_foundation_soberana_v1(
        {
            "topic_seed": "clareza, disciplina e direção",
            "headline": "Sem disciplina, clareza perde força antes de virar resultado.",
            "hook": "O problema raramente é falta de esforço. Quase sempre é mover muito sem critério suficiente.",
            "body": "Quando estrutura entra, intenção deixa de depender do humor do dia e a execução passa a responder a processo.",
            "support_points": [
                "Clareza sem base vira intenção solta.",
                "Disciplina protege consistência quando o entusiasmo cai.",
            ],
            "cta": "Salve para revisar antes da próxima decisão.",
            "format_recommendation": "image",
            "series_name": "Liberta a Verdade",
        }
    )
    rejected_payload = build_visual_foundation_soberana_v1(
        {
            "topic_seed": "motivação",
            "headline": "Acredite em você e tudo vai mudar hoje mesmo agora para sempre",
            "hook": "Descubra o segredo antes que seja tarde porque ninguém te conta isso e tudo pode ser diferente agora",
            "body": "Sua vida pode mudar. Basta querer. Compartilhe com todo mundo porque esse conteúdo é imperdível e viral.",
            "support_points": [
                "Mais foco.",
                "Mais resultado.",
                "Mais energia.",
            ],
            "cta": "Comente aqui agora",
            "format_recommendation": "image",
            "series_name": "Liberta a Verdade",
        }
    )
    return {
        "ok": True,
        "approved_example": evaluate_visual_hierarchy_gate(approved_payload),
        "rejected_example": evaluate_visual_hierarchy_gate(rejected_payload),
    }
