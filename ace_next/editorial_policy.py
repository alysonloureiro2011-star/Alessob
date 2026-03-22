from __future__ import annotations

import re
from typing import Any

POLICY_VERSION = "foundation_editorial_model_v1"
BRAND_PERSONA = "editorial soberano, lúcido, disciplinado, claro, firme, humano e anti-commodity"
TONE_OF_VOICE = [
    "clareza antes de volume",
    "autoridade sem arrogância",
    "tensão ética sem sensacionalismo",
    "densidade com legibilidade",
    "naturalidade sem clichê motivacional",
]

FORBIDDEN_PATTERNS = [
    "descubra o segredo",
    "mude sua vida hoje",
    "você precisa",
    "clique no link",
    "viral",
    "imperdível",
    "nunca antes",
    "transforme sua vida agora",
    "basta querer",
    "acredite em você",
]

REJECTION_FLAGS = [
    "coach_generic",
    "commodity_language",
    "cheap_ai_tone",
    "mechanical_progression",
    "weak_cta",
]

BRAND_LEXICON = [
    "clareza",
    "direção",
    "disciplina",
    "critério",
    "consistência",
    "execução",
    "verdade",
    "presença",
    "autoridade",
    "valor real",
    "leitura",
    "prática",
    "processo",
    "posicionamento",
]

CTA_PATTERNS = [
    "salve",
    "envie",
    "compartilhe",
    "releia",
    "use isso",
]


def get_editorial_policy() -> dict[str, Any]:
    return {
        "version": POLICY_VERSION,
        "brand_persona": BRAND_PERSONA,
        "tone_of_voice": list(TONE_OF_VOICE),
        "forbidden_patterns": list(FORBIDDEN_PATTERNS),
        "brand_lexicon": list(BRAND_LEXICON),
        "rejection_flags": list(REJECTION_FLAGS),
        "cta_patterns": list(CTA_PATTERNS),
    }


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).lower()


def detect_forbidden_patterns(text: str) -> list[str]:
    normalized = normalize_text(text)
    hits: list[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in normalized and pattern not in hits:
            hits.append(pattern)
    return hits


def lexicon_hits(text: str) -> list[str]:
    normalized = normalize_text(text)
    hits: list[str] = []
    for term in BRAND_LEXICON:
        if term in normalized and term not in hits:
            hits.append(term)
    return hits


def detect_rejection_flags(*, headline: str, hook: str, body: str, cta: str) -> list[str]:
    text = normalize_text(" ".join([headline, hook, body, cta]))
    flags: list[str] = []

    if any(term in text for term in ["acredite", "sonhe", "destrave sua vida", "seja sua melhor versão"]):
        flags.append("coach_generic")
    if any(term in text for term in ["viral", "imperdível", "segredo", "fórmula"]):
        flags.append("commodity_language")
    if len(body.split(". ")) < 2:
        flags.append("mechanical_progression")
    if len(cta.strip()) < 24:
        flags.append("weak_cta")
    if any(term in text for term in ["transforme sua vida agora", "nunca antes", "descubra o segredo"]):
        flags.append("cheap_ai_tone")

    return flags
