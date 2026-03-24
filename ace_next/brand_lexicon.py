from __future__ import annotations

import re
import unicodedata
from typing import Any


BRAND_NAME = "Liberta a Verdade"

BRAND_VOICE = [
    "clareza antes de volume",
    "autoridade sem arrogância",
    "densidade com legibilidade",
    "tensão ética sem sensacionalismo",
    "naturalidade sem frase inflada",
    "lucidez acima de performance verbal",
]

ANTI_VOICE = [
    "coach genérico",
    "copy commodity",
    "motivacional vazio",
    "ameaça apelativa",
    "frase bonita sem consequência",
    "promessa inflada",
    "teatralidade vazia",
]

APPROVED_LANGUAGE_PATTERNS = [
    "o problema raramente está onde parece",
    "quase sempre o custo nasce antes do colapso",
    "sem estrutura, intenção não sustenta resultado",
    "clareza reorganiza prioridade",
    "disciplina protege direção",
    "valor percebido nasce de utilidade real",
]

DISALLOWED_PATTERNS = [
    "descubra o segredo",
    "mude sua vida hoje",
    "você precisa",
    "antes que seja tarde",
    "nunca antes",
    "imperdível",
    "viral",
    "basta querer",
    "acredite em você",
    "sua melhor versão",
    "pare de sofrer agora",
    "transforme sua vida agora",
]

SEMANTIC_ANCHORS = [
    "clareza",
    "direção",
    "disciplina",
    "critério",
    "consistência",
    "execução",
    "estrutura",
    "processo",
    "verdade",
    "lucidez",
    "prioridade",
    "eixo",
    "presença",
    "posicionamento",
    "valor real",
]

TENSION_ANCHORS = [
    "custo oculto",
    "erro silencioso",
    "travamento",
    "leitura errada",
    "desgaste",
    "ruído",
    "reação automática",
    "pressa sem base",
]

CLARITY_ANCHORS = [
    "na prática",
    "em vez de",
    "o problema é",
    "o centro é",
    "isso muda quando",
    "o efeito real é",
]

PERCEIVED_VALUE_ANCHORS = [
    "serve para decisão real",
    "vira critério",
    "reduz ruído",
    "melhora leitura",
    "organiza prioridade",
    "aumenta nitidez",
]

APPROVED_CTA_PATTERNS = [
    "salve para reler",
    "salve para revisar",
    "envie para alguém",
    "compartilhe com quem",
    "releia isso antes",
    "use isso como régua",
]

DISALLOWED_CTA_PATTERNS = [
    "comente aqui",
    "marca alguém",
    "corre",
    "clique no link",
    "compartilhe com todo mundo",
    "segue para mais",
]


def normalize_text(value: str) -> str:
    value = re.sub(r"\s+", " ", (value or "").strip()).lower()
    value = "".join(
        char for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )
    return value


def get_brand_lexicon() -> dict[str, Any]:
    return {
        "brand_name": BRAND_NAME,
        "brand_voice": list(BRAND_VOICE),
        "anti_voice": list(ANTI_VOICE),
        "approved_language_patterns": list(APPROVED_LANGUAGE_PATTERNS),
        "disallowed_patterns": list(DISALLOWED_PATTERNS),
        "semantic_anchors": list(SEMANTIC_ANCHORS),
        "tension_anchors": list(TENSION_ANCHORS),
        "clarity_anchors": list(CLARITY_ANCHORS),
        "perceived_value_anchors": list(PERCEIVED_VALUE_ANCHORS),
        "approved_cta_patterns": list(APPROVED_CTA_PATTERNS),
        "disallowed_cta_patterns": list(DISALLOWED_CTA_PATTERNS),
    }


def scan_brand_alignment(text: str, lexicon: dict[str, Any] | None = None) -> dict[str, list[str]]:
    lexicon = lexicon or get_brand_lexicon()
    normalized = normalize_text(text)

    def _hits(items: list[str]) -> list[str]:
        found: list[str] = []
        for item in items:
            if normalize_text(item) in normalized and item not in found:
                found.append(item)
        return found

    return {
        "approved_language_patterns": _hits(list(lexicon.get("approved_language_patterns", []))),
        "disallowed_patterns": _hits(list(lexicon.get("disallowed_patterns", []))),
        "semantic_anchors": _hits(list(lexicon.get("semantic_anchors", []))),
        "tension_anchors": _hits(list(lexicon.get("tension_anchors", []))),
        "clarity_anchors": _hits(list(lexicon.get("clarity_anchors", []))),
        "perceived_value_anchors": _hits(list(lexicon.get("perceived_value_anchors", []))),
        "approved_cta_patterns": _hits(list(lexicon.get("approved_cta_patterns", []))),
        "disallowed_cta_patterns": _hits(list(lexicon.get("disallowed_cta_patterns", []))),
    }
