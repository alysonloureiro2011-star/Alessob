
import random
import re
import unicodedata


TREND_POOL = [
    "disciplina e prosperidade",
    "clareza e propósito",
    "controle emocional",
    "renovação da mente",
    "fé e propósito",
    "mentalidade próspera",
    "transformação de vida",
    "escassez e abundância",
]


def normalize_trend(text):
    text = str(text or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def choose_trend():
    return random.choice(TREND_POOL)


def pick_trend():
    return choose_trend()


def get_trend():
    return choose_trend()


def build_trend_object(topic=None, score=1.0):
    topic = topic or choose_trend()
    return {
        "topic": topic,
        "trend": topic,
        "trend_norm": normalize_trend(topic),
        "score": float(score),
    }
