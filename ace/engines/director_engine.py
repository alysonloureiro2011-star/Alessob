import random
import datetime


STYLE_POOL = [
    "filosofico",
    "provocativo",
    "reflexivo",
    "direto",
    "espiritual"
]


def pick_style_by_trend(trend):
    trend = (trend or "").lower()

    if any(x in trend for x in ["fé", "deus", "jesus", "davi", "bíblia", "biblica", "espiritual"]):
        return "espiritual"

    if any(x in trend for x in ["disciplina", "prosperidade", "clareza", "propósito", "proposito"]):
        return random.choice(["filosofico", "direto", "provocativo"])

    if any(x in trend for x in ["ansiedade", "dor", "emocional", "mente", "mental"]):
        return random.choice(["reflexivo", "filosofico"])

    return random.choice(STYLE_POOL)


def pick_content_type(trend):
    trend = (trend or "").lower()

    if any(x in trend for x in ["disciplina", "prosperidade", "clareza", "propósito", "proposito"]):
        return random.choice(["carrossel", "reel"])

    if any(x in trend for x in ["ansiedade", "controle emocional", "mente", "mental"]):
        return random.choice(["reel", "carrossel"])

    return random.choice(["reel", "carrossel"])


def build_director_plan(trend):
    content_type = pick_content_type(trend)
    style = pick_style_by_trend(trend)

    return {
        "trend": trend,
        "style": style,
        "content_type": content_type,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
