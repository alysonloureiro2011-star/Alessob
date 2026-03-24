from __future__ import annotations

import re
from typing import Any

from .brand_ontology import get_brand_ontology, ontology_lexicon_hits


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip()).lower()


def _bounded(value: float) -> float:
    return max(0.0, min(round(value, 2), 10.0))


def evaluate_caption_comprehension(
    headline: str,
    hook: str,
    body: str,
    cta: str,
    ontology: dict | None = None,
) -> dict:
    ontology = ontology or get_brand_ontology()

    headline_n = _normalize(headline)
    hook_n = _normalize(hook)
    body_n = _normalize(body)
    cta_n = _normalize(cta)
    full_text = " ".join([headline_n, hook_n, body_n, cta_n])

    flags: list[str] = []
    reasons: list[str] = []

    forbidden_hits = []
    for pattern in ontology.get("forbidden_patterns", []):
        if _normalize(pattern) in full_text:
            forbidden_hits.append(pattern)

    if forbidden_hits:
        flags.append("forbidden_patterns")
        reasons.append("foram detectados padrões proibidos da marca")

    if any(term in full_text for term in ["acredite", "mude sua vida", "sua melhor versão", "destrave sua vida"]):
        flags.append("coach_generic")
        reasons.append("o texto cai em coach genérico")

    if any(term in full_text for term in ["segredo", "imperdível", "viral", "fórmula", "antes que seja tarde"]):
        flags.append("commodity_language")
        reasons.append("o texto soa commodity/apelativo")

    if len(set(full_text.split())) < 18:
        flags.append("low_semantic_variety")
        reasons.append("o texto está curto ou pouco denso semanticamente")

    if len(cta_n) < 28 or any(term in cta_n for term in ["comente aqui", "marca alguém", "corre"]):
        flags.append("weak_cta")
        reasons.append("o CTA ainda está fraco ou genérico")

    if len(body_n.split(". ")) < 2:
        flags.append("thin_body")
        reasons.append("o body ainda não sustenta progressão suficiente")

    lexicon_hits = ontology_lexicon_hits(full_text, ontology)

    clarity = 6.0
    if len(headline_n) >= 28:
        clarity += 1.0
    if len(hook_n) >= 80:
        clarity += 1.0
    if len(body_n) >= 150:
        clarity += 1.0
    if "?" not in headline_n:
        clarity += 0.5
    clarity = _bounded(clarity)

    semantic_density = 5.5 + min(len(lexicon_hits), 3) * 1.1
    if len(set(full_text.split())) >= 28:
        semantic_density += 1.0
    semantic_density = _bounded(semantic_density)

    naturality = 6.0
    if not forbidden_hits:
        naturality += 1.0
    if "!" not in full_text:
        naturality += 0.8
    if "você precisa" not in full_text:
        naturality += 0.7
    naturality = _bounded(naturality)

    anti_commodity = 5.5
    if "commodity_language" not in flags:
        anti_commodity += 2.0
    if "coach_generic" not in flags:
        anti_commodity += 1.0
    anti_commodity = _bounded(anti_commodity)

    anti_generic = 5.5
    if len(lexicon_hits) >= 2:
        anti_generic += 1.5
    if len(set(full_text.split())) >= 24:
        anti_generic += 1.0
    if "coach_generic" not in flags:
        anti_generic += 1.0
    anti_generic = _bounded(anti_generic)

    cta_quality = 5.5
    if any(cta_n.startswith(prefix) for prefix in ["salve", "envie", "compartilhe", "releia", "use isso"]):
        cta_quality += 1.5
    if len(cta_n) >= 45:
        cta_quality += 1.0
    if "weak_cta" not in flags:
        cta_quality += 1.0
    cta_quality = _bounded(cta_quality)

    score = round(
        (
            clarity
            + semantic_density
            + naturality
            + anti_commodity
            + anti_generic
            + cta_quality
        )
        / 6
        * 10,
        2,
    )

    approved = (
        clarity >= 8.0
        and anti_generic >= 8.0
        and anti_commodity >= 8.0
        and naturality >= 7.5
        and cta_quality >= 7.0
        and "forbidden_patterns" not in flags
        and "coach_generic" not in flags
        and "commodity_language" not in flags
    )

    if approved and not reasons:
        reasons.append("caption clara, densa, natural e alinhada à marca")

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
        "lexicon_hits": lexicon_hits,
    }
