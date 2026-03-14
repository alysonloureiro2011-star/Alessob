import random


FALLBACK_TRENDS = [
    "disciplina e prosperidade",
    "controle emocional",
    "renovação da mente",
    "transformação mental",
    "clareza e propósito",
    "ansiedade e paz",
    "escassez e abundância",
    "fé e propósito",
    "verdade bíblica",
    "mentalidade próspera"
]


def build_trend_object(topic, score=1.0):
    return {
        "topic": str(topic).strip(),
        "score": float(score)
    }


def fetch_google_trends():
    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="pt-BR", tz=180)
        trending = pytrends.trending_searches(pn="brazil")

        topics = trending[0].tolist()
        trends = []

        for topic in topics[:10]:
            topic = str(topic).strip()
            if topic:
                trends.append(
                    build_trend_object(topic, score=random.uniform(0.7, 1.4))
                )

        if trends:
            return trends

    except Exception:
        pass

    return [
        build_trend_object(random.choice(FALLBACK_TRENDS), 1.0)
    ]


def pick_best_trend():
    trends = fetch_google_trends()

    if not trends:
        return build_trend_object(random.choice(FALLBACK_TRENDS), 1.0)

    ranked = sorted(trends, key=lambda x: x["score"], reverse=True)
    return ranked[0]


def choose_trend():
    return pick_best_trend()["topic"]
