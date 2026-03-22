from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

STOPWORDS = {
    "a",
    "ao",
    "aos",
    "as",
    "às",
    "com",
    "como",
    "da",
    "das",
    "de",
    "do",
    "dos",
    "e",
    "é",
    "em",
    "mais",
    "menos",
    "na",
    "nas",
    "no",
    "nos",
    "o",
    "os",
    "ou",
    "para",
    "por",
    "que",
    "se",
    "sem",
    "sobre",
    "um",
    "uma",
    "uns",
    "umas",
}

WEAK_INPUTS = {
    "",
    "123",
    "aaa",
    "hello",
    "oi",
    "test",
    "teste",
    "teste real",
}

SERIES_NAME = "Liberta a Verdade"
VISUAL_STYLE = "visual_foundation_pack_v1"
PUBLISH_STYLE = "official_next_visual_foundation_v1"
STRATEGIC_TARGET_FORMAT = "reel_premium"
PUBLISH_FORMAT_NOW = "image"


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


def _clean_text(value: str) -> str:
    value = (value or "").strip()
    return re.sub(r"\s+", " ", value)


def _strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(char)
    )


def _normalize(value: str) -> str:
    return _strip_accents(_clean_text(value)).lower()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _normalize(value))


def _topic_seed(trend: str) -> str:
    clean = _clean_text(trend)
    if _normalize(clean) in WEAK_INPUTS:
        return "clareza, disciplina e direção"
    return clean or "clareza, disciplina e direção"


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


def _dedupe_keep_order(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        cleaned = _clean_text(value)
        if cleaned and cleaned not in unique:
            unique.append(cleaned)
    return unique


def _infer_family(keywords: list[str]) -> str:
    base = {_normalize(word) for word in keywords if _normalize(word)}

    families = {
        "faith": {"fe", "proposito", "deus", "jesus", "biblia", "espiritual", "oracao"},
        "discipline": {"disciplina", "foco", "clareza", "execucao", "consistencia", "direcao", "resultado"},
        "emotion": {"ansiedade", "medo", "mente", "emocional", "emocao", "paz", "controle"},
        "prosperity": {"prosperidade", "riqueza", "financeiro", "financeira", "abundancia", "escassez", "dinheiro"},
        "branding": {"marca", "conteudo", "instagram", "autoridade", "posicionamento", "comunicacao"},
    }

    best_family = "editorial"
    best_hits = 0
    for family, family_words in families.items():
        hits = len(base & family_words)
        if hits > best_hits:
            best_hits = hits
            best_family = family

    return best_family


def _choose_color_profile(keywords: list[str]) -> str:
    family = _infer_family(keywords)
    if family in {"discipline", "emotion", "branding"}:
        return "electric_blue"
    if family == "prosperity":
        return "amber_gold"
    return "editorial_violet"


def _core_words(keywords: list[str]) -> tuple[str, str, str]:
    primary = keywords[0] if len(keywords) > 0 else "clareza"
    secondary = keywords[1] if len(keywords) > 1 else "disciplina"
    tertiary = keywords[2] if len(keywords) > 2 else "direção"
    return primary, secondary, tertiary


def _family_blocks(topic: str, keywords: list[str]) -> dict[str, str | list[str]]:
    family = _infer_family(keywords)
    primary, secondary, tertiary = _core_words(keywords)

    if family == "faith":
        objective = "transformar um tema espiritual em mensagem clara, forte e aplicável"
        angle = (
            f"{topic} ganha força quando deixa de ser emoção solta e vira convicção com prática diária."
        )
        hook = (
            f"O erro silencioso é querer viver {primary} sem construir {secondary}. "
            f"A intenção até existe, mas a vida continua puxando para o automático."
        )
        headline = f"Sem {secondary}, até {primary} perde força no cotidiano."
        body = (
            f"Quando {primary} não encontra rotina, ela vira só impulso passageiro. "
            f"Quando {secondary} entra em cena, a decisão ganha constância. "
            f"E quando {tertiary} assume o centro, o tema deixa de ser discurso bonito e começa a orientar vida real."
        )
        support_points = [
            f"{primary.capitalize()} sem prática vira só emoção.",
            f"{secondary.capitalize()} sustenta convicção nos dias comuns.",
            f"{tertiary.capitalize()} protege a decisão quando o ânimo oscila.",
        ]
        cta = "Salve para revisar depois e envie para alguém que precisa alinhar convicção com prática."
    elif family == "emotion":
        objective = "dar clareza emocional sem cair em linguagem vaga ou terapêutica genérica"
        angle = (
            f"{topic} melhora quando a pessoa para de reagir no impulso e volta a organizar leitura, ritmo e resposta."
        )
        hook = (
            f"Muita gente acha que o problema é o peso de {primary}. "
            f"Na prática, o que costuma agravar tudo é atravessar isso sem {secondary}."
        )
        headline = f"Sem {secondary}, {primary} toma conta do dia inteiro."
        body = (
            f"Sem {secondary}, qualquer ruído parece urgência. "
            f"Com {tertiary}, a mente volta a enxergar prioridade antes de reagir. "
            f"O resultado é menos desgaste, mais domínio interno e uma resposta muito mais inteligente."
        )
        support_points = [
            f"{secondary.capitalize()} reduz reação automática.",
            f"{tertiary.capitalize()} devolve leitura antes da resposta.",
            f"{primary.capitalize()} perde força quando o eixo interno volta ao lugar.",
        ]
        cta = "Salve para reler quando a mente acelerar e mande para quem precisa recuperar eixo hoje."
    elif family == "prosperity":
        objective = "elevar valor percebido com linguagem de construção, processo e maturidade"
        angle = (
            f"{topic} cresce melhor com leitura, consistência e decisão firme do que com ansiedade e pressa."
        )
        hook = (
            f"O travamento raramente está na falta de vontade. "
            f"Na maioria das vezes, ele nasce de perseguir {primary} sem construir {secondary}."
        )
        headline = f"Sem {secondary}, {primary} vira só expectativa."
        body = (
            f"Resultado não responde bem a urgência desorganizada. "
            f"Ele responde melhor quando {secondary} sustenta processo e {tertiary} organiza foco. "
            f"É isso que tira o tema do desejo abstrato e aproxima da execução real."
        )
        support_points = [
            f"{secondary.capitalize()} reduz desperdício de energia e recurso.",
            f"{tertiary.capitalize()} protege o foco contra distração e ansiedade.",
            f"{primary.capitalize()} fica mais concreto quando a base é previsível.",
        ]
        cta = "Salve isso como referência de execução e compartilhe com quem precisa trocar pressa por construção."
    elif family == "branding":
        objective = "transformar o tema em posicionamento forte, legível e menos commodity"
        angle = (
            f"{topic} fica mais forte quando abandona volume vazio e assume direção, identidade e utilidade real."
        )
        hook = (
            f"O problema quase nunca é falta de conteúdo. "
            f"O problema é produzir {primary} sem critério, sem {secondary} e sem uma leitura clara de {tertiary}."
        )
        headline = f"Sem {secondary}, {primary} parece só mais do mesmo."
        body = (
            f"Marca não cresce com excesso de postagem sem eixo. "
            f"Ela cresce quando a mensagem tem direção, quando a forma reforça a ideia e quando o público percebe valor rápido. "
            f"É assim que o conteúdo deixa de parecer commodity e começa a carregar identidade."
        )
        support_points = [
            f"{secondary.capitalize()} separa posicionamento de volume vazio.",
            f"{tertiary.capitalize()} aumenta nitidez de mensagem e de público.",
            f"{primary.capitalize()} só ganha força quando carrega utilidade e identidade.",
        ]
        cta = "Salve para usar como régua editorial e envie para quem precisa subir o padrão da comunicação."
    else:
        objective = "entregar uma peça editorial mais clara, forte e útil, sem cara de template"
        angle = (
            f"{topic} melhora quando sai da frase bonita e entra em critério, prática e decisão repetível."
        )
        hook = (
            f"O que mais trava resultado normalmente não é falta de esforço. "
            f"É tentar sustentar {primary} sem {secondary}."
        )
        headline = f"Sem {secondary}, {primary} perde força antes de virar resultado."
        body = (
            f"Ideia boa sozinha não sustenta mudança. "
            f"Ela precisa de {secondary} para ganhar forma e de {tertiary} para não se perder no meio do caminho. "
            f"Quando isso acontece, o tema deixa de soar abstrato e começa a servir para a vida real."
        )
        support_points = [
            f"{primary.capitalize()} sem base vira intenção solta.",
            f"{secondary.capitalize()} sustenta execução quando o entusiasmo cai.",
            f"{tertiary.capitalize()} organiza prioridade e protege consistência.",
        ]
        cta = "Salve para revisar na próxima decisão e envie para alguém que precisa de mais direção e menos ruído."

    return {
        "family": family,
        "objective": objective,
        "angle": angle,
        "hook": hook,
        "headline": headline,
        "body": body,
        "support_points": support_points,
        "cta": cta,
    }


def _hashtags(keywords: list[str], family: str) -> list[str]:
    base_tags = [f"#{_slug(word)}" for word in keywords if _slug(word)]

    family_tags = {
        "faith": ["#proposito", "#conviccao", "#direcao"],
        "emotion": ["#clarezamental", "#controleemocional", "#equilibrio"],
        "prosperity": ["#prosperidade", "#execucao", "#consistencia"],
        "discipline": ["#disciplina", "#foco", "#direcao"],
        "branding": ["#posicionamento", "#autoridade", "#conteudocomproposito"],
        "editorial": ["#clareza", "#estrategia", "#direcao"],
    }

    tags = base_tags + family_tags.get(family, []) + ["#libertaaverdade", "#mentalidade", "#valorreal"]
    return _dedupe_keep_order(tags)[:8]


def _build_first_comment(topic: str, support_points: list[str], hashtags: list[str]) -> str:
    opening = f"Qual parte disso mais pega em você hoje em {topic}?"
    proof = support_points[0] if support_points else "Clareza muda execução."
    tail = " ".join(hashtags[:4])
    return f"{opening} {proof} {tail}".strip()


def _score_text(
    *,
    topic: str,
    hook: str,
    headline: str,
    body: str,
    support_points: list[str],
    cta: str,
    hashtags: list[str],
) -> int:
    score = 60

    if len(topic) >= 12:
        score += 3
    if len(headline) >= 24:
        score += 6
    if len(hook) >= 90:
        score += 6
    if len(body) >= 160:
        score += 7
    if len(support_points) >= 3:
        score += 5
    if len(hashtags) >= 6:
        score += 3

    normalized_text = _normalize(" ".join([topic, hook, headline, body, cta] + support_points))
    strong_signals = {
        "clareza",
        "consistencia",
        "criterio",
        "direcao",
        "execucao",
        "foco",
        "pratica",
        "resultado",
    }
    token_hits = len({token for token in strong_signals if token in normalized_text})
    score += min(token_hits * 2, 8)

    commodity_flags = [
        "descubra",
        "imperdivel",
        "incrivel",
        "mude sua vida agora",
        "clique",
        "viral",
    ]
    if any(flag in normalized_text for flag in commodity_flags):
        score -= 12

    if _normalize(topic) in WEAK_INPUTS:
        score = min(score, 60)

    return max(52, min(score, 92))


def build_creative_plan(trend: str) -> CreativePlan:
    clean_input = _clean_text(trend)
    topic = _topic_seed(clean_input)
    keywords = _keywords(topic)

    blocks = _family_blocks(topic, keywords)
    family = str(blocks["family"])
    objective = str(blocks["objective"])
    angle = str(blocks["angle"])
    hook = str(blocks["hook"])
    headline = str(blocks["headline"])
    body = str(blocks["body"])
    support_points = [str(item) for item in blocks["support_points"]]
    cta = str(blocks["cta"])

    hashtags = _hashtags(keywords, family)
    first_comment = _build_first_comment(topic, support_points, hashtags)

    quality_score = _score_text(
        topic=topic,
        hook=hook,
        headline=headline,
        body=body,
        support_points=support_points,
        cta=cta,
        hashtags=hashtags,
    )

    caption = (
        f"{hook}\n\n"
        f"{headline}\n\n"
        f"{body}\n\n"
        f"Pontos de apoio:\n"
        f"• {support_points[0]}\n"
        f"• {support_points[1]}\n"
        f"• {support_points[2]}\n\n"
        f"{cta}\n\n"
        f"{' '.join(hashtags[:5])}"
    )

    notes = [
        f"editorial_family={family}",
        "planner=rebuild_v2",
        "hook_mode=tension_plus_clarity",
        "cta_mode=practical_share_save",
        "distribution=hashtags_plus_first_comment",
    ]

    return CreativePlan(
        trend_input=clean_input,
        topic_seed=topic,
        series_name=SERIES_NAME,
        objective=objective,
        strategic_target_format=STRATEGIC_TARGET_FORMAT,
        publish_format_now=PUBLISH_FORMAT_NOW,
        angle=angle,
        hook=hook,
        headline=headline,
        body=body,
        support_points=support_points,
        caption=caption,
        first_comment=first_comment,
        hashtags=hashtags,
        cta=cta,
        visual_style=VISUAL_STYLE,
        color_profile=_choose_color_profile(keywords),
        publish_style=PUBLISH_STYLE,
        quality_score=quality_score,
        notes=notes,
    )
