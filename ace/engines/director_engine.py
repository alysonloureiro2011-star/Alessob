import random

STYLE_POOL = [
    "filosofico",
    "provocativo",
    "reflexivo",
    "direto",
    "espiritual"
]

CONTENT_POOL = [
    "reel",
    "carrossel",
    "imagem"
]


def choose_style(trend=None):
    trend = (trend or "").lower()

    if any(x in trend for x in ["fé", "deus", "jesus", "bíblia", "espiritual"]):
        return "espiritual"

    if any(x in trend for x in ["disciplina", "prosperidade", "clareza", "propósito"]):
        return random.choice(["filosofico", "direto", "provocativo"])

    if any(x in trend for x in ["ansiedade", "dor", "emocional", "mente"]):
        return random.choice(["reflexivo", "filosofico"])

    return random.choice(STYLE_POOL)


def choose_content_type(trend=None):
    trend = (trend or "").lower()

    if any(x in trend for x in ["disciplina", "prosperidade", "clareza"]):
        return "carrossel"

    if any(x in trend for x in ["emocional", "mente", "ansiedade"]):
        return "reel"

    return random.choice(CONTENT_POOL)


def build_director_plan(trend):
    style = choose_style(trend)
    content_type = choose_content_type(trend)

    return {
        "trend": trend,
        "style": style,
        "content_type": content_type
    }
