import random
import re
import time
from typing import Dict, List


class TrendGovernor:

    def __init__(self):

        self.recent_trends: List[str] = []
        self.max_memory = 20

    # --------------------------------------------------
    # LIMPEZA DE TREND
    # --------------------------------------------------

    def normalize(self, trend: str) -> str:

        trend = trend.lower()
        trend = re.sub(r"[^\w\s]", "", trend)
        trend = re.sub(r"\s+", " ", trend)

        return trend.strip()

    # --------------------------------------------------
    # SCORE DE TREND
    # --------------------------------------------------

    def score(self, trend: str) -> float:

        score = 0.0

        # tamanho da frase
        score += min(len(trend) / 20, 1)

        # palavras fortes
        power_words = [
            "segredo",
            "erro",
            "verdade",
            "ninguém",
            "descubra",
            "choque",
            "urgente"
        ]

        for p in power_words:
            if p in trend:
                score += 1

        score += random.uniform(0.1, 0.9)

        return score

    # --------------------------------------------------
    # ANTI DUPLICAÇÃO
    # --------------------------------------------------

    def is_duplicate(self, trend: str) -> bool:

        normalized = self.normalize(trend)

        for old in self.recent_trends:
            if normalized == old:
                return True

        return False

    # --------------------------------------------------
    # REGISTRAR TREND
    # --------------------------------------------------

    def register(self, trend: str):

        normalized = self.normalize(trend)

        self.recent_trends.append(normalized)

        if len(self.recent_trends) > self.max_memory:
            self.recent_trends.pop(0)

    # --------------------------------------------------
    # SELECIONAR TREND
    # --------------------------------------------------

    def choose(self, trends: List[str]) -> Dict:

        candidates = []

        for t in trends:

            if not t:
                continue

            if self.is_duplicate(t):
                continue

            s = self.score(t)

            candidates.append((t, s))

        if not candidates:
            return {
                "trend": random.choice(trends),
                "score": 0.1,
                "timestamp": time.time()
            }

        candidates.sort(key=lambda x: x[1], reverse=True)

        best = candidates[0]

        self.register(best[0])

        return {
            "trend": best[0],
            "score": best[1],
            "timestamp": time.time()
        }


trend_governor = TrendGovernor()
