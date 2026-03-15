import random
import time
from typing import Dict


CONTENT_TYPES = [
    "reel",
    "carrossel"
]

STYLES = [
    "choque",
    "curiosidade",
    "segredo",
    "historia",
    "autoridade"
]

INTENSITY = [
    "leve",
    "media",
    "forte"
]


class DecisionEngine:

    def __init__(self):

        self.last_decisions = []

    # --------------------------------------------------

    def choose_content_type(self) -> str:

        return random.choice(CONTENT_TYPES)

    # --------------------------------------------------

    def choose_style(self) -> str:

        return random.choice(STYLES)

    # --------------------------------------------------

    def choose_intensity(self) -> str:

        return random.choice(INTENSITY)

    # --------------------------------------------------

    def build_decision(self, trend_object: Dict) -> Dict:

        trend = trend_object.get("trend")

        decision = {
            "trend": trend,
            "content_type": self.choose_content_type(),
            "style": self.choose_style(),
            "intensity": self.choose_intensity(),
            "timestamp": time.time()
        }

        self.last_decisions.append(decision)

        if len(self.last_decisions) > 50:
            self.last_decisions.pop(0)

        return decision


decision_engine = DecisionEngine()
