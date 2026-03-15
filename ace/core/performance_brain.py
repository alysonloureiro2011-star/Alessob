from typing import Dict, List, Optional


class PerformanceBrain:

    def __init__(self):
        self.memory: List[Dict] = []
        self.max_memory = 500

    # --------------------------------------------------
    # score principal
    # --------------------------------------------------

    def compute_score(
        self,
        likes: float = 0.0,
        comments: float = 0.0,
        shares: float = 0.0,
        saves: float = 0.0,
        reach: float = 0.0,
        retention: float = 0.0
    ) -> float:

        reach_base = max(reach, 1.0)

        engagement_score = (
            (likes * 1.0) +
            (comments * 2.0) +
            (shares * 3.0) +
            (saves * 3.0)
        ) / reach_base

        retention_score = retention * 2.5

        final_score = engagement_score + retention_score

        return round(final_score, 6)

    # --------------------------------------------------
    # registra resultado
    # --------------------------------------------------

    def register_result(
        self,
        trend: str,
        content_type: str,
        style: str,
        angle: str,
        likes: float = 0.0,
        comments: float = 0.0,
        shares: float = 0.0,
        saves: float = 0.0,
        reach: float = 0.0,
        retention: float = 0.0,
        quality_score: float = 0.0,
        publish_ok: bool = True
    ) -> Dict:

        performance_score = self.compute_score(
            likes=likes,
            comments=comments,
            shares=shares,
            saves=saves,
            reach=reach,
            retention=retention
        )

        record = {
            "trend": trend,
            "content_type": content_type,
            "style": style,
            "angle": angle,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "reach": reach,
            "retention": retention,
            "quality_score": quality_score,
            "publish_ok": publish_ok,
            "performance_score": performance_score
        }

        self.memory.append(record)

        if len(self.memory) > self.max_memory:
            self.memory.pop(0)

        return record

    # --------------------------------------------------
    # melhores padrões
    # --------------------------------------------------

    def top_trends(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("trend", limit)

    def top_formats(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("content_type", limit)

    def top_styles(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("style", limit)

    def top_angles(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("angle", limit)

    def _aggregate_by_key(self, key: str, limit: int = 5) -> List[Dict]:
        bucket = {}

        for item in self.memory:
            value = item.get(key)
            if not value:
                continue

            if value not in bucket:
                bucket[value] = {
                    "name": value,
                    "count": 0,
                    "total_score": 0.0,
                    "avg_score": 0.0
                }

            bucket[value]["count"] += 1
            bucket[value]["total_score"] += float(item.get("performance_score", 0.0))

        output = []
        for _, data in bucket.items():
            count = max(data["count"], 1)
            data["avg_score"] = round(data["total_score"] / count, 6)
            output.append(data)

        output.sort(key=lambda x: x["avg_score"], reverse=True)

        return output[:limit]

    # --------------------------------------------------
    # resumo geral
    # --------------------------------------------------

    def summary(self) -> Dict:
        total = len(self.memory)

        if total == 0:
            return {
                "total_records": 0,
                "avg_performance_score": 0.0,
                "avg_quality_score": 0.0,
                "publish_failures": 0,
                "top_trends": [],
                "top_formats": [],
                "top_styles": [],
                "top_angles": []
            }

        avg_perf = sum(float(x.get("performance_score", 0.0)) for x in self.memory) / total
        avg_quality = sum(float(x.get("quality_score", 0.0)) for x in self.memory) / total
        failures = sum(1 for x in self.memory if not x.get("publish_ok", True))

        return {
            "total_records": total,
            "avg_performance_score": round(avg_perf, 6),
            "avg_quality_score": round(avg_quality, 6),
            "publish_failures": failures,
            "top_trends": self.top_trends(),
            "top_formats": self.top_formats(),
            "top_styles": self.top_styles(),
            "top_angles": self.top_angles()
        }

    # --------------------------------------------------
    # tendência de melhora ou piora
    # --------------------------------------------------

    def recent_trend_direction(self, window: int = 10) -> str:
        if len(self.memory) < max(window, 4):
            return "insufficient_data"

        recent = self.memory[-window:]
        first_half = recent[: len(recent) // 2]
        second_half = recent[len(recent) // 2 :]

        avg_first = sum(float(x.get("performance_score", 0.0)) for x in first_half) / max(len(first_half), 1)
        avg_second = sum(float(x.get("performance_score", 0.0)) for x in second_half) / max(len(second_half), 1)

        if avg_second > avg_first * 1.10:
            return "improving"

        if avg_second < avg_first * 0.90:
            return "declining"

        return "stable"

    # --------------------------------------------------
    # recomendação simples
    # --------------------------------------------------

    def recommend_focus(self) -> Dict:
        top_format = self.top_formats(limit=1)
        top_style = self.top_styles(limit=1)
        top_angle = self.top_angles(limit=1)
        top_trend = self.top_trends(limit=1)

        return {
            "best_format": top_format[0]["name"] if top_format else None,
            "best_style": top_style[0]["name"] if top_style else None,
            "best_angle": top_angle[0]["name"] if top_angle else None,
            "best_trend": top_trend[0]["name"] if top_trend else None,
            "direction": self.recent_trend_direction()
        }


performance_brain = PerformanceBrain()
