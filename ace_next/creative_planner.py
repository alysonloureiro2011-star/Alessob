from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

STOPWORDS = {
    "a", "o", "e", "de", "da", "do", "das", "dos", "em", "na", "no", "nas", "nos",
    "para", "por", "com", "sem", "um", "uma", "uns", "umas", "que", "é", "se",
    "ao", "aos", "às", "as", "os", "mais", "menos", "sobre", "como",
}

WEAK_INPUTS = {"teste", "teste real", "test", "oi", "hello", "aaa", "123"}


def _clean_text(value: str) -> str:
    value = (value or "").strip()
    return re.sub(r"\s+", " ", value)


def _topic_seed(trend: str) -> str:
    value = _clean_text(trend).lower()
    if not value or value in WEAK_INPUTS:
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
    return unique[:8]


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


def _choose_color_profile(keywords: list[str]) -> str:
    if any(word in {"clareza", "foco", "disciplina", "direção"} for word in keywords):
        return "electric_blue"
    if any(word in {"crescimento", "resultado", "execução"} for word in keywords):
        return "amber_gold"
    return "editorial_violet"


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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_creative_plan(trend: str) -> CreativePlan:
    clean_input = _clean_text(trend)
    topic = _topic_seed(clean_input)
    keywords = _keywords(topic)

    primary = keywords[0] if keywords else "clareza"
    secondary = keywords[1] if len(keywords) > 1 else "disciplina"
    tertiary = keywords[2] if len(keywords) > 2 else "direção"

    hook = f"O que trava o resultado quase sempre não é esforço. É {primary} sem {secondary}."
    headline = f"Sem {primary}, esforço vira ruído."
    body = (
        f"Quando existe {primary}, a decisão ganha nitidez. "
        f"Quando existe {secondary}, o movimento deixa de ser aleatório."
    )
    angle = (
        f"Troque impulso por {tertiary}. "
        f"Menos volume, mais clareza, repetição e consistência."
    )

    support_points = [
        f"{primary.capitalize()} reduz desperdício.",
        f"{secondary.capitalize()} sustenta execução.",
        f"{tertiary.capitalize()} organiza prioridade.",
    ]

    hashtags = _hashtags(keywords)
    cta = "Salve este insight e envie para quem precisa disso hoje."

    caption = (
        f"{hook}\n\n"
        f"{body}\n\n"
        f"{angle}\n\n"
        f"{cta}\n\n"
        f"{' '.join(hashtags[:5])}"
    )

    first_comment = " ".join(hashtags)

    weak_input = clean_input.lower() in WEAK_INPUTS
    quality_score = 58 if weak_input else 76

    return CreativePlan(
        trend_input=clean_input,
        topic_seed=topic,
        series_name="Liberta a Verdade",
        objective="tirar o card de teste do placeholder visual e elevar valor percebido",
        strategic_target_format="reel_premium",
        publish_format_now="image",
        angle=angle,
        hook=hook,
        headline=headline,
        body=body,
        support_points=support_points,
        caption=caption,
        first_comment=first_comment,
        hashtags=hashtags,
        cta=cta,
        visual_style="visual_foundation_pack_v1",
        color_profile=_choose_color_profile(keywords),
        publish_style="official_next_visual_foundation_v1",
        quality_score=quality_score,
        notes=[
            "bloco visual foundation pack v1 ativo",
            "formato estratégico alvo = reel premium",
            "formato operacional atual = imagem única",
        ],
    )
