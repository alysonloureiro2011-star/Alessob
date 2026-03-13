import random
import datetime


def choose_content_type():

    hour = datetime.datetime.now().hour

    if hour in [6,7,8,11,12,13]:
        return "reel"

    if hour in [18,19,20,21]:
        return "carrossel"

    return random.choice([
        "reel",
        "carrossel"
    ])


def choose_style():

    styles = [
        "reflexivo",
        "direto",
        "provocativo",
        "filosofico",
        "estrategico"
    ]

    return random.choice(styles)


def build_director_plan(trend):

    return {
        "trend": trend,
        "content_type": choose_content_type(),
        "style": choose_style(),
        "created_at": datetime.datetime.utcnow().isoformat()
    }
