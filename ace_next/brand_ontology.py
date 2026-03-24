from __future__ import annotations

from typing import Any

from .editorial_examples import get_approved_examples, get_rejected_examples
from .editorial_policy import (
    BRAND_LEXICON,
    BRAND_PERSONA,
    CTA_PATTERNS,
    FORBIDDEN_PATTERNS,
    POLICY_VERSION,
    TONE_OF_VOICE,
)


def get_brand_ontology() -> dict[str, Any]:
    return {
        "version": "brand_ontology_v1",
        "policy_version": POLICY_VERSION,
        "brand_name": "Liberta a Verdade",
        "brand_persona": BRAND_PERSONA,
        "voice": list(TONE_OF_VOICE)
        + [
            "clareza com densidade",
            "autoridade com naturalidade",
            "tensão com utilidade",
            "insight antes de efeito",
            "frase forte sem teatralidade",
        ],
        "anti_voice": [
            "coach genérico",
            "copy commodity",
            "promessa inflada",
            "urgência apelativa",
            "motivacional vazio",
            "frase bonita sem insight",
            "autoridade artificial",
        ],
        "lexicon": list(BRAND_LEXICON)
        + [
            "estrutura",
            "eixo",
            "lucidez",
            "posse mental",
            "domínio interno",
            "hierarquia",
            "base real",
            "valor percebido",
        ],
        "forbidden_patterns": list(FORBIDDEN_PATTERNS),
        "cta_families": [
            {
                "name": "save_and_return",
                "examples": [
                    "Salve para reler quando a mente começar a dispersar.",
                    "Salve isso como régua para a próxima decisão importante.",
                ],
            },
            {
                "name": "share_with_precision",
                "examples": [
                    "Envie para alguém que precisa recuperar critério antes de reagir.",
                    "Compartilhe com quem precisa trocar pressa por estrutura.",
                ],
            },
            {
                "name": "revisit_and_apply",
                "examples": [
                    "Releia isso antes de decidir no impulso.",
                    "Use isso como filtro prático nas próximas 24 horas.",
                ],
            },
        ],
        "hook_families": [
            {
                "name": "hidden_cost",
                "description": "mostrar o custo silencioso de continuar igual",
                "starters": [
                    "O problema raramente está onde parece.",
                    "Quase sempre o travamento nasce antes do resultado ruim aparecer.",
                ],
            },
            {
                "name": "misread_reality",
                "description": "mostrar que a leitura atual do problema está errada ou incompleta",
                "starters": [
                    "Muita gente chama isso de falta de força, mas o erro é outro.",
                    "Você não está lidando com falta de vontade. Está lidando com falta de leitura.",
                ],
            },
            {
                "name": "discipline_reframe",
                "description": "reorganizar esforço, disciplina e consistência como estrutura",
                "starters": [
                    "Sem estrutura, até boa intenção se desfaz no ruído.",
                    "Sem direção, esforço demais vira desgaste e não avanço.",
                ],
            },
            {
                "name": "identity_break",
                "description": "romper a identidade fraca e propor eixo mais forte",
                "starters": [
                    "Tem coisa que parece personalidade, mas é só padrão mal consolidado.",
                    "Nem todo impulso merece comando sobre o seu dia.",
                ],
            },
        ],
        "narrative_rules": [
            "começar com fricção ou custo oculto",
            "nomear o problema sem abstração vazia",
            "trazer insight que reorganiza a leitura",
            "fechar com payoff cognitivo",
            "usar CTA útil, não mendigado",
        ],
        "pattern_interrupt_rules": [
            "a quebra de padrão deve ser consciente, ética e auditável",
            "não usar susto vazio, mentira, pressão falsa ou manipulação obscura",
            "priorizar contraste semântico sobre gritaria",
        ],
        "serial_rules": [
            "uma peça forte deve abrir espaço para continuação",
            "continuação não é repetição literal; é aprofundamento, contraste ou aplicação",
            "cada peça deve poder gerar parte 2 sem parecer caça-clique",
        ],
        "approved_examples": get_approved_examples(),
        "rejected_examples": get_rejected_examples(),
        "approved_example_ids": [item["id"] for item in get_approved_examples()],
        "rejected_example_ids": [item["id"] for item in get_rejected_examples()],
        "cta_patterns": list(CTA_PATTERNS),
    }


def ontology_lexicon_hits(text: str, ontology: dict[str, Any] | None = None) -> list[str]:
    ontology = ontology or get_brand_ontology()
    normalized = (text or "").lower()
    hits: list[str] = []
    for term in ontology.get("lexicon", []):
        if str(term).lower() in normalized and term not in hits:
            hits.append(term)
    return hits
