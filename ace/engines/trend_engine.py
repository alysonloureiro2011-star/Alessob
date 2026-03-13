import random
import datetime


def choose_trend(trends):
    """
    Escolhe uma trend baseada em score.
    """
    if not trends:
        return None

    try:
        trends = sorted(trends, key=lambda t: t.get("score", 0), reverse=True)
    except Exception:
        return None

    top = trends[:5] if len(trends) > 5 else trends

    return random.choice(top)


def normalize_trend(text):
    """
    Normaliza texto de trend.
    """
    if not text:
        return None

    return str(text).lower().strip()


def build_trend_object(topic, score=1.0):
    """
    Cria objeto de trend padronizado.
    """
    return {
        "topic": topic,
        "score": float(score),
        "created_at": datetime.datetime.utcnow().isoformat()
    }
def fetch_google_trends():

    try:
        from pytrends.request import TrendReq

        pytrends = TrendReq(hl="pt-BR", tz=180)

        trending = pytrends.trending_searches(pn="brazil")

        topics = trending[0].tolist()

        trends = []

        for topic in topics[:10]:

            trends.append(
                build_trend_object(topic, score=random.uniform(0.5, 1.5))
            )

        return trends

    except Exception as e:

        print("Erro ao buscar trends:", e)

        return [
            build_trend_object("inteligencia artificial", 1.0)
        ]
