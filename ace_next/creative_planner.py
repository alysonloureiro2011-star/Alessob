from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

STOPWORDS = {
    "a", "o", "e", "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "para", "por", "com", "sem", "um", "uma", "uns", "umas", "que", "é", "se",
    "ao", "aos", "às", "as", "os", "mais", "menos", "sobre", "como", "real", "teste"
}


def _clean_text(value: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"\s+", " ", value)
    return value


def _topic_seed(trend: str) -> str:
    value = _clean_text(trend).lower()
    if not value or value in {"teste", "teste real", "test"}:
        return "clareza, disciplina e direção"
    return value


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
    return unique[:6]


def _title_case(value: str) -> str:
    return " ".join(part.capitalize() for part in _clean_text(value).split())


def _hashtags(keywords: list[str]) -> list[str]:
    tags: list[str] = []
    for word in keywords:
        safe = re.sub(r"[^a-zA-ZÀ-ÿ0-9]", "", word)
        if not safe:
            continue
        tag = f"#{safe}"
        if tag not in tags:
            tags.append(tag)
    base = ["#instagram", "#conteudo", "#estrategia"]
    for item in base:
        if item not in tags:
            tags.append(item)
    return tags[:8]


@dataclass
class CreativePlan:
    trend_input: str
    topic_seed: str
    objective: str
    strategic_target_format: str
    publish_format_now: str
    angle: str
    hook: str
    headline: str
    body: str
    caption: str
    first_comment: str
    hashtags: list[str]
    cta: str
    visual_style: str
    publish_style: str
    quality_score: int
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_creative_plan(trend: str) -> CreativePlan:
    topic = _topic_seed(trend)
    words = _keywords(topic)
    primary = words[0] if words else "clareza"
    secondary = words[1] if len(words) > 1 else "direção"

    headline = _title_case(f"{primary} muda o resultado")
    hook = f"O que trava o resultado quase sempre não é esforço. É {primary} sem {secondary}."
    body = (
        f"Quando existe {primary}, a decisão fica mais limpa. "
        f"Quando existe {secondary}, o movimento deixa de ser aleatório."
    )
    angle = (
        f"Tratar {topic} como direção e não como impulso. "
        f"Menos volume, mais clareza, repetição e consistência."
    )
    cta = "Salve este insight e envie para quem precisa disso hoje."
    tags = _hashtags(words)

    caption = (
        f"{hook}\n\n"
        f"{angle}\n\n"
        f"{cta}\n\n"
        f"{' '.join(tags[:5])}"
    )

    first_comment = " ".join(tags)

    return CreativePlan(
        trend_input=_clean_text(trend),
        topic_seed=topic,
        objective="publicar peça simples, mais legível e com valor editorial mínimo",
        strategic_target_format="reel_premium",
        publish_format_now="image",
        angle=angle,
        hook=hook,
        headline=headline,
        body=body,
        caption=caption,
        first_comment=first_comment,
        hashtags=tags,
        cta=cta,
        visual_style="clean_high_contrast_editorial_card",
        publish_style="official_next_editorial_v1",
        quality_score=62,
        notes=[
            "formato estratégico alvo = reel premium",
            "formato operacional atual = imagem única",
            "planner heurístico para reduzir post cru de teste",
        ],
    )
