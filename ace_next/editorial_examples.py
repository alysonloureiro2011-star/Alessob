from __future__ import annotations

from typing import Any

APPROVED_EXAMPLES = [
    {
        "id": "approved_01",
        "headline": "Sem direção, até esforço de verdade se perde no ruído.",
        "hook": "O travamento raramente nasce da falta de vontade. Ele nasce de mover muito sem critério suficiente.",
        "why": "tem tensão, clareza, progressão e valor percebido",
    },
    {
        "id": "approved_02",
        "headline": "Quando a clareza sobe, a ansiedade perde comando.",
        "hook": "Nem toda pressão vem do mundo. Muita coisa piora quando a mente reage antes de ler o que está acontecendo.",
        "why": "é humano, forte, legível e anti-commodity",
    },
    {
        "id": "approved_03",
        "headline": "Marca forte não nasce de volume vazio. Nasce de leitura e direção.",
        "hook": "O problema raramente é falta de conteúdo. O problema é produzir sem identidade, sem recorte e sem hierarquia de mensagem.",
        "why": "soa editorial, não coach, e sustenta posicionamento",
    },
]

REJECTED_EXAMPLES = [
    {
        "id": "rejected_01",
        "headline": "Acredite em você e tudo vai mudar.",
        "hook": "Descubra o segredo para destravar sua vida hoje.",
        "why": "genérico, coach, commodity e fraco para marca",
    },
    {
        "id": "rejected_02",
        "headline": "Pare de sofrer agora.",
        "hook": "Você precisa ver isso antes que seja tarde.",
        "why": "manipulativo, apelativo e anti-brand",
    },
    {
        "id": "rejected_03",
        "headline": "Mais foco, mais resultado.",
        "hook": "Salve isso e compartilhe com todo mundo.",
        "why": "raso demais, sem densidade e sem progressão",
    },
]


def get_approved_examples() -> list[dict[str, Any]]:
    return list(APPROVED_EXAMPLES)


def get_rejected_examples() -> list[dict[str, Any]]:
    return list(REJECTED_EXAMPLES)


def examples_context(topic: str) -> dict[str, Any]:
    topic = (topic or "").lower()
    approved_ids = [item["id"] for item in APPROVED_EXAMPLES[:2]]
    rejected_ids = [item["id"] for item in REJECTED_EXAMPLES[:2]]

    if any(term in topic for term in ["marca", "conteúdo", "instagram", "autoridade"]):
        approved_ids = ["approved_03", "approved_01"]
        rejected_ids = ["rejected_03", "rejected_01"]
    elif any(term in topic for term in ["ansiedade", "mente", "emocional", "medo"]):
        approved_ids = ["approved_02", "approved_01"]
        rejected_ids = ["rejected_02", "rejected_03"]

    return {
        "approved_examples": [item for item in APPROVED_EXAMPLES if item["id"] in approved_ids],
        "rejected_examples": [item for item in REJECTED_EXAMPLES if item["id"] in rejected_ids],
        "approved_ids": approved_ids,
        "rejected_ids": rejected_ids,
    }
