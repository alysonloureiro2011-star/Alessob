from __future__ import annotations

from typing import Any

from .brand_lexicon import get_brand_lexicon, normalize_text, scan_brand_alignment


def _bounded(value: float) -> float:
    return max(0.0, min(round(value, 2), 10.0))


def evaluate_caption_comprehension(
    headline: str,
    hook: str,
    body: str,
    cta: str,
    lexicon: dict | None = None,
) -> dict[str, Any]:
    lexicon = lexicon or get_brand_lexicon()

    headline_n = normalize_text(headline)
    hook_n = normalize_text(hook)
    body_n = normalize_text(body)
    cta_n = normalize_text(cta)
    full_text = " ".join([headline_n, hook_n, body_n, cta_n]).strip()

    alignment = scan_brand_alignment(full_text, lexicon)

    flags: list[str] = []
    reasons: list[str] = []

    if alignment["disallowed_patterns"]:
        flags.append("disallowed_patterns")
        reasons.append("foram detectados padrões proibidos pela marca")

    if alignment["disallowed_cta_patterns"]:
        flags.append("weak_cta")
        reasons.append("o CTA usa padrões frouxos ou genéricos")

    if len(body_n.split()) < 22:
        flags.append("abstracao_excessiva")
        reasons.append("o body está curto demais para sustentar consequência real")

    if len(set(full_text.split())) < 18:
        flags.append("frase_bonita_sem_consequencia")
        reasons.append("o texto tem pouca densidade semântica")

    if any(term in full_text for term in ["acredite", "merece mais", "destrave sua vida", "melhor versão"]):
        flags.append("coach_commodity")
        reasons.append("o texto caiu em coach barato")

    if not alignment["tension_anchors"] and not any(
        term in full_text for term in ["erro", "custo", "travamento", "ruido", "desgaste", "quase sempre"]
    ):
        flags.append("tensao_fraca")
        reasons.append("faltou tensão narrativa suficiente")

    clarity = 5.5
    if len(headline_n) >= 28:
        clarity += 1.0
    if len(hook_n) >= 90:
        clarity += 1.0
    if len(body_n) >= 170:
        clarity += 1.1
    if alignment["clarity_anchors"]:
        clarity += 1.1
    clarity = _bounded(clarity)

    semantic_density = 5.0
    semantic_density += min(len(alignment["semantic_anchors"]) * 0.9, 2.7)
    semantic_density += min(len(set(full_text.split())) / 25.0, 1.6)
    semantic_density = _bounded(semantic_density)

    naturality = 5.8
    if not alignment["disallowed_patterns"]:
        naturality += 1.2
    if "!" not in full_text:
        naturality += 0.7
    if len(body_n.split(". ")) >= 2:
        naturality += 0.9
    if "você precisa" not in full_text:
        naturality += 0.8
    naturality = _bounded(naturality)

    anti_commodity = 5.0
    if not alignment["disallowed_patterns"]:
        anti_commodity += 1.8
    if not alignment["disallowed_cta_patterns"]:
        anti_commodity += 1.0
    if not any(term in full_text for term in ["viral", "segredo", "imperdivel", "formula"]):
        anti_commodity += 1.2
    anti_commodity = _bounded(anti_commodity)

    anti_generic = 5.0
    anti_generic += min(len(alignment["semantic_anchors"]) * 0.7, 2.1)
    if alignment["approved_language_patterns"]:
        anti_generic += 1.0
    if not any(term in full_text for term in ["melhor versao", "mude sua vida", "acredite em voce"]):
        anti_generic += 1.0
    anti_generic = _bounded(anti_generic)

    cta_quality = 5.0
    if alignment["approved_cta_patterns"]:
        cta_quality += 2.0
    if len(cta_n) >= 45:
        cta_quality += 1.0
    if not alignment["disallowed_cta_patterns"]:
        cta_quality += 1.0
    cta_quality = _bounded(cta_quality)

    score = round(
        ((clarity + semantic_density + naturality + anti_commodity + anti_generic + cta_quality) / 6) * 10,
        2,
    )

    approved = (
        clarity >= 8.0
        and anti_generic >= 8.0
        and anti_commodity >= 8.0
        and naturality >= 7.5
        and cta_quality >= 7.0
        and "disallowed_patterns" not in flags
        and "coach_commodity" not in flags
    )

    if approved and not reasons:
        reasons.append("caption clara, forte e alinhada à marca")

    return {
        "ok": True,
        "approved": approved,
        "score": score,
        "flags": flags,
        "reasons": reasons,
        "breakdown": {
            "clarity": clarity,
            "semantic_density": semantic_density,
            "naturality": naturality,
            "anti_commodity": anti_commodity,
            "anti_generic": anti_generic,
            "cta_quality": cta_quality,
        },
        "alignment": alignment,
    }


def caption_gate_examples() -> dict[str, Any]:
    lexicon = get_brand_lexicon()
    rejected = evaluate_caption_comprehension(
        headline="Acredite em você e tudo vai mudar",
        hook="Descubra o segredo que ninguém te conta",
        body="Você merece mais. Sua vida pode mudar agora.",
        cta="Comente aqui",
        lexicon=lexicon,
    )
    approved = evaluate_caption_comprehension(
        headline="Sem disciplina, clareza perde força antes de virar resultado.",
        hook="O travamento raramente nasce da falta de esforço. Quase sempre nasce de mover muito sem critério suficiente.",
        body="Quando falta estrutura, intenção não sustenta consistência. O ponto não é parecer forte. O ponto é construir leitura, prioridade e execução repetível.",
        cta="Salve para revisar antes da próxima decisão e envie para alguém que precisa de mais eixo e menos ruído.",
        lexicon=lexicon,
    )
    return {"ok": True, "approved_example": approved, "rejected_example": rejected}
