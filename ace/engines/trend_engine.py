
import random
import datetime

def choose_trend(trends):
    """
    Escolhe uma trend baseada em score.
    """
    if not trends:
        return None

    trends = sorted(trends, key=lambda t: t.get("score", 0), reverse=True)

    top = trends[:5]

    return random.choice(top)


def normalize_trend(text):
    if not text:
        return None

    return text.lower().strip()


def build_trend_object(topic, score=1.0):
    return {
        "topic": topic,
        "score": score,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
