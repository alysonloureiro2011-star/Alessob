from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from typing import Any

from .editorial_examples import examples_context
from .editorial_policy import BRAND_PERSONA, POLICY_VERSION, TONE_OF_VOICE, get_editorial_policy, lexicon_hits
from .editorial_rubric import evaluate_editorial_quality

STOPWORDS = {
    "a", "ao", "aos", "as", "às", "com", "como", "da", "das", "de", "do", "dos", "e", "é",
    "em", "mais", "menos", "na", "nas", "no", "nos", "o", "os", "ou", "para", "por", "que",
    "se", "sem", "sobre", "um", "uma", "uns", "umas",
}

WEAK_INPUTS = {"", "123", "aaa", "hello", "oi", "test", "teste", "teste real"}
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
    policy_version: str
    brand_persona: str
    tone_of_voice: list[str]
    brand_lexicon_hits: list[str]
    approved_example_ids: list[str]
    rejected_example_ids: list[str]
    editorial_score_breakdown: dict[str, int]
    editorial_reasons: list[str]
    editorial_flags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value or "") if not unicodedata.combining(char)
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


def _family(keywords: list[str]) -> str:
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
    for name, terms in families.items():
        hits = len(base & terms)
        if hits > best_hits:
            best_hits = hits
            best_family = name
    return best_family


def _choose_color_profile(keywords: list[str]) -> str:
    family = _family(keywords)
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


def _editorial_blocks(topic: str, keywords: list[str]) -> dict[str, str | list[str]]:
    family = _family(keywords)
    primary, secondary, tertiary = _core_words(keywords)

    if family == "faith":
        objective = "transformar tema espiritual em mensagem clara, firme e aplicável"
        angle = f"{topic} fica mais forte quando sai do impulso emocional e entra em convicção com prática diária."
        hook = (
            f"Muita gente deseja viver {primary}, mas continua no automático porque tenta sustentar isso sem {secondary}. "
            f"A intenção existe, só que ainda falta estrutura para virar postura real."
        )
        headline = f"Sem {secondary}, até {primary} perde força no cotidiano."
        body = (
            f"Quando {primary} fica solta, ela vira emoção passageira. Quando {secondary} entra, a decisão ganha continuidade. "
            f"E quando {tertiary} passa a conduzir a rotina, o tema deixa de ser discurso bonito e começa a organizar vida real."
        )
        support_points = [
            f"{primary.capitalize()} sem prática vira só impulso.",
            f"{secondary.capitalize()} sustenta convicção nos dias comuns.",
            f"{tertiary.capitalize()} protege a decisão quando a emoção oscila.",
        ]
        cta = "Salve para reler depois e envie para alguém que precisa alinhar convicção com prática diária."
    elif family == "emotion":
        objective = "dar clareza emocional sem cair em linguagem terapêutica genérica"
        angle = f"{topic} melhora quando a pessoa para de reagir no impulso e volta a organizar leitura, ritmo e resposta."
        hook = (
            f"Nem sempre o peso de {primary} é o problema principal. Muitas vezes o que piora tudo é atravessar isso sem {secondary}, "
            f"como se toda pressão tivesse a mesma urgência."
        )
        headline = f"Sem {secondary}, {primary} toma conta do dia inteiro."
        body = (
            f"Sem {secondary}, qualquer ruído parece ameaça. Com {tertiary}, a mente volta a enxergar prioridade antes da resposta. "
            f"O efeito não é perfeição instantânea. É menos desgaste, mais domínio interno e uma leitura muito mais lúcida do que realmente importa."
        )
        support_points = [
            f"{secondary.capitalize()} reduz reação automática.",
            f"{tertiary.capitalize()} devolve leitura antes da resposta.",
            f"{primary.capitalize()} perde força quando o eixo interno volta ao lugar.",
        ]
        cta = "Salve para usar como lembrete de eixo e mande para quem precisa recuperar clareza hoje."
    elif family == "prosperity":
        objective = "elevar valor percebido com linguagem de construção, processo e maturidade"
        angle = f"{topic} não cresce bem com ansiedade desorganizada. Cresce melhor com leitura, consistência e execução repetível."
        hook = (
            f"O travamento quase nunca está na falta de vontade. Na maioria das vezes ele nasce de buscar {primary} sem construir {secondary}, "
            f"como se desejo já fosse base suficiente para sustentar resultado."
        )
        headline = f"Sem {secondary}, {primary} vira só expectativa."
        body = (
            f"Resultado responde melhor a processo do que a pressa. Quando {secondary} sustenta a base e {tertiary} organiza prioridade, "
            f"o tema deixa de soar abstrato e começa a entrar no território da execução concreta."
        )
        support_points = [
            f"{secondary.capitalize()} reduz desperdício de energia e recurso.",
            f"{tertiary.capitalize()} protege foco contra distração e ansiedade.",
            f"{primary.capitalize()} fica mais concreto quando a base é previsível.",
        ]
        cta = "Salve isso como régua de execução e compartilhe com quem precisa trocar pressa por construção."
    elif family == "branding":
        objective = "transformar o tema em posicionamento forte, legível e menos commodity"
        angle = f"{topic} fica mais forte quando abandona volume vazio e assume identidade, recorte e utilidade real."
        hook = (
            f"O problema raramente é falta de conteúdo. O problema é produzir {primary} sem critério, sem {secondary} "
            f"e sem uma leitura clara de {tertiary}."
        )
        headline = f"Sem {secondary}, {primary} parece só mais do mesmo."
        body = (
            f"Marca não cresce com excesso de postagem sem eixo. Ela cresce quando a mensagem tem direção, quando a forma reforça a ideia "
            f"e quando o público percebe valor rápido. É assim que o conteúdo deixa de parecer commodity e começa a carregar identidade."
        )
        support_points = [
            f"{secondary.capitalize()} separa posicionamento de volume vazio.",
            f"{tertiary.capitalize()} aumenta nitidez de mensagem e de público.",
            f"{primary.capitalize()} só ganha força quando carrega utilidade e identidade.",
        ]
        cta = "Salve para usar como régua editorial e envie para quem precisa subir o padrão da comunicação."
    else:
        objective = "entregar uma peça editorial mais clara, forte e útil, sem cara de template"
        angle = f"{topic} melhora quando sai da frase bonita e entra em critério, prática e decisão repetível."
        hook = (
            f"O que mais trava resultado normalmente não é falta de esforço. É tentar sustentar {primary} sem {secondary}, "
            f"como se intenção sozinha conseguisse segurar consistência ao longo do tempo."
        )
        headline = f"Sem {secondary}, {primary} perde força antes de virar resultado."
        body = (
            f"Ideia boa sozinha não sustenta mudança. Ela precisa de {secondary} para ganhar forma e de {tertiary} para não se perder no meio do caminho. "
            f"Quando isso acontece, o tema deixa de soar abstrato e começa a servir para decisões reais."
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
    tags = [f"#{_slug(word)}" for word in keywords if _slug(word)]
    family_tags = {
        "faith": ["#proposito", "#conviccao", "#direcao"],
        "emotion": ["#clarezamental", "#controleemocional", "#equilibrio"],
        "prosperity": ["#prosperidade", "#execucao", "#consistencia"],
        "discipline": ["#disciplina", "#foco", "#direcao"],
        "branding": ["#posicionamento", "#autoridade", "#conteudocomcriterio"],
        "editorial": ["#clareza", "#estrategia", "#direcao"],
    }
    tags.extend(family_tags.get(family, []))
    tags.extend(["#libertaaverdade", "#valorreal", "#mentalidade"])
    unique: list[str] = []
    for tag in tags:
        if tag and tag not in unique:
            unique.append(tag)
    return unique[:8]


def _first_comment(topic: str, support_points: list[str], hashtags: list[str]) -> str:
    opening = f"Qual parte disso mais pesa hoje em {topic}?"
    proof = support_points[0] if support_points else "Clareza muda execução."
    return f"{opening} {proof} {' '.join(hashtags[:4])}".strip()


def build_creative_plan(trend: str) -> CreativePlan:
    policy = get_editorial_policy()
    clean_input = _clean_text(trend)
    topic = _topic_seed(clean_input)
    keywords = _keywords(topic)
    blocks = _editorial_blocks(topic, keywords)
    examples = examples_context(topic)

    family = str(blocks["family"])
    objective = str(blocks["objective"])
    angle = str(blocks["angle"])
    hook = str(blocks["hook"])
    headline = str(blocks["headline"])
    body = str(blocks["body"])
    support_points = [str(item) for item in blocks["support_points"]]
    cta = str(blocks["cta"])
    hashtags = _hashtags(keywords, family)
    first_comment = _first_comment(topic, support_points, hashtags)

    draft_plan = {
        "trend_input": clean_input,
        "topic_seed": topic,
        "headline": headline,
        "hook": hook,
        "body": body,
        "support_points": support_points,
        "cta": cta,
        "hashtags": hashtags,
    }
    editorial_qa = evaluate_editorial_quality(draft_plan)

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
        f"policy={POLICY_VERSION}",
        f"editorial_family={family}",
        "foundation_editorial_model_v1_active",
        "planner_mode=anti_cliche_anti_commodity",
        "strategic_target=reel_premium",
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
        quality_score=editorial_qa.final_score,
        notes=notes,
        policy_version=policy["version"],
        brand_persona=BRAND_PERSONA,
        tone_of_voice=list(TONE_OF_VOICE),
        brand_lexicon_hits=lexicon_hits(" ".join([headline, hook, body, cta] + support_points)),
        approved_example_ids=list(examples["approved_ids"]),
        rejected_example_ids=list(examples["rejected_ids"]),
        editorial_score_breakdown=dict(editorial_qa.breakdown),
        editorial_reasons=list(editorial_qa.reasons),
        editorial_flags=list(editorial_qa.flags),
    )
