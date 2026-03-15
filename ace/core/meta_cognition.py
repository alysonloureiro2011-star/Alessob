import time
from typing import Dict, List


class MetaCognitionEngine:

    def __init__(self):
        self.reflections: List[Dict] = []
        self.max_memory = 100

    def evaluate_cycle(
        self,
        trend: str,
        content_type: str,
        style: str,
        performance_score: float,
        quality_score: float,
        publish_ok: bool
    ) -> Dict:

        status = "good"
        if not publish_ok:
            status = "failure"
        elif performance_score < 0.4:
            status = "weak"
        elif performance_score > 0.75 and quality_score > 0.75:
            status = "strong"

        reflection = {
            "timestamp": time.time(),
            "trend": trend,
            "content_type": content_type,
            "style": style,
            "performance_score": performance_score,
            "quality_score": quality_score,
            "publish_ok": publish_ok,
            "status": status
        }

        self.reflections.append(reflection)

        if len(self.reflections) > self.max_memory:
            self.reflections.pop(0)

        return reflection

    def summarize(self) -> Dict:
        total = len(self.reflections)

        if total == 0:
            return {
                "total_cycles": 0,
                "strong": 0,
                "weak": 0,
                "failure": 0,
                "dominant_pattern": None
            }

        strong = sum(1 for r in self.reflections if r["status"] == "strong")
        weak = sum(1 for r in self.reflections if r["status"] == "weak")
        failure = sum(1 for r in self.reflections if r["status"] == "failure")

        trend_count = {}
        for r in self.reflections:
            t = r["trend"]
            trend_count[t] = trend_count.get(t, 0) + 1

        dominant_pattern = max(trend_count, key=trend_count.get) if trend_count else None

        return {
            "total_cycles": total,
            "strong": strong,
            "weak": weak,
            "failure": failure,
            "dominant_pattern": dominant_pattern
        }

    def should_shift_strategy(self) -> bool:
        if len(self.reflections) < 5:
            return False

        recent = self.reflections[-5:]
        weak_or_fail = sum(1 for r in recent if r["status"] in ("weak", "failure"))

        return weak_or_fail >= 4


meta_cognition_engine = MetaCogniti
