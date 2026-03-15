import random
from typing import Dict, List


class HypothesisEngine:

    def __init__(self):

        self.hypotheses: List[Dict] = []

    # -----------------------------------------

    def generate(self, trend: str, format_type: str):

        possible_angles = [

            "choque de verdade",
            "revelação inesperada",
            "conflito moral",
            "curiosidade extrema",
            "paradoxo psicológico",
            "erro comum das pessoas",
            "verdade que poucos aceitam"
        ]

        angle = random.choice(possible_angles)

        hypothesis = {

            "trend": trend,
            "format": format_type,
            "angle": angle,
            "confidence": 0.5,
            "tests": 0,
            "wins": 0
        }

        self.hypotheses.append(hypothesis)

        return hypothesis

    # -----------------------------------------

    def update(self, hypothesis: Dict, performance_score: float):

        hypothesis["tests"] += 1

        if performance_score > 0.7:
            hypothesis["wins"] += 1

        if hypothesis["tests"] > 0:
            hypothesis["confidence"] = hypothesis["wins"] / hypothesis["tests"]

    # -----------------------------------------

    def best_hypotheses(self):

        ordered = sorted(
            self.hypotheses,
            key=lambda h: h["confidence"],
            reverse=True
        )

        return ordered[:5]


hypothesis_engine = HypothesisEngine()
