from typing import Dict, List, Optional


class StudioMemory:

    def __init__(self):
        self.records: List[Dict] = []
        self.max_records = 1000

    # --------------------------------------------------
    # registrar ciclo completo
    # --------------------------------------------------

    def register(
        self,
        trend: str,
        content_type: str,
        style: str,
        angle: str,
        intensity: Optional[str] = None,
        visual_mood: Optional[str] = None,
        camera_style: Optional[str] = None,
        lighting: Optional[str] = None,
        palette: Optional[str] = None,
        rhythm: Optional[str] = None,
        quality_score: float = 0.0,
        performance_score: float = 0.0,
        publish_ok: bool = True
    ) -> Dict:

        record = {
            "trend": trend,
            "content_type": content_type,
            "style": style,
            "angle": angle,
            "intensity": intensity,
            "visual_mood": visual_mood,
            "camera_style": camera_style,
            "lighting": lighting,
            "palette": palette,
            "rhythm": rhythm,
            "quality_score": float(quality_score),
            "performance_score": float(performance_score),
            "publish_ok": bool(publish_ok)
        }

        self.records.append(record)

        if len(self.records) > self.max_records:
            self.records.pop(0)

        return record

    # --------------------------------------------------
    # agregação genérica
    # --------------------------------------------------

    def _aggregate_by_key(self, key: str, limit: int = 5) -> List[Dict]:
        bucket = {}

        for item in self.records:
            value = item.get(key)
            if not value:
                continue

            if value not in bucket:
                bucket[value] = {
                    "name": value,
                    "count": 0,
                    "total_quality": 0.0,
                    "total_performance": 0.0,
                    "avg_quality": 0.0,
                    "avg_performance": 0.0,
                    "success_rate": 0.0,
                    "publish_success": 0
                }

            bucket[value]["count"] += 1
            bucket[value]["total_quality"] += float(item.get("quality_score", 0.0))
            bucket[value]["total_performance"] += float(item.get("performance_score", 0.0))

            if item.get("publish_ok", True):
                bucket[value]["publish_success"] += 1

        output = []

        for _, data in bucket.items():
            count = max(data["count"], 1)
            data["avg_quality"] = round(data["total_quality"] / count, 6)
            data["avg_performance"] = round(data["total_performance"] / count, 6)
            data["success_rate"] = round(data["publish_success"] / count, 6)
            output.append(data)

        output.sort(
            key=lambda x: (
                x["avg_performance"] * 0.55 +
                x["avg_quality"] * 0.30 +
                x["success_rate"] * 0.15
            ),
            reverse=True
        )

        return output[:limit]

    # --------------------------------------------------
    # memórias principais
    # --------------------------------------------------

    def best_trends(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("trend", limit)

    def best_formats(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("content_type", limit)

    def best_styles(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("style", limit)

    def best_angles(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("angle", limit)

    def best_visual_moods(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("visual_mood", limit)

    def best_palettes(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("palette", limit)

    def best_camera_styles(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("camera_style", limit)

    def best_rhythms(self, limit: int = 5) -> List[Dict]:
        return self._aggregate_by_key("rhythm", limit)

    # --------------------------------------------------
    # combinação vencedora
    # --------------------------------------------------

    def best_combination(self) -> Optional[Dict]:
        if not self.records:
            return None

        scored = []

        for item in self.records:
            composite = (
                float(item.get("performance_score", 0.0)) * 0.6 +
                float(item.get("quality_score", 0.0)) * 0.4
            )

            scored.append({
                "trend": item.get("trend"),
                "content_type": item.get("content_type"),
                "style": item.get("style"),
                "angle": item.get("angle"),
                "intensity": item.get("intensity"),
                "visual_mood": item.get("visual_mood"),
                "camera_style": item.get("camera_style"),
                "lighting": item.get("lighting"),
                "palette": item.get("palette"),
                "rhythm": item.get("rhythm"),
                "score": round(composite, 6),
                "publish_ok": item.get("publish_ok", True)
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[0]

    # --------------------------------------------------
    # resumo global
    # --------------------------------------------------

    def summary(self) -> Dict:
        total = len(self.records)

        if total == 0:
            return {
                "total_records": 0,
                "best_trends": [],
                "best_formats": [],
                "best_styles": [],
                "best_angles": [],
                "best_visual_moods": [],
                "best_palettes": [],
                "best_camera_styles": [],
                "best_rhythms": [],
                "best_combination": None
            }

        return {
            "total_records": total,
            "best_trends": self.best_trends(),
            "best_formats": self.best_formats(),
            "best_styles": self.best_styles(),
            "best_angles": self.best_angles(),
            "best_visual_moods": self.best_visual_moods(),
            "best_palettes": self.best_palettes(),
            "best_camera_styles": self.best_camera_styles(),
            "best_rhythms": self.best_rhythms(),
            "best_combination": self.best_combination()
        }

    # --------------------------------------------------
    # recomendação operacional
    # --------------------------------------------------

    def recommend_next_setup(self) -> Dict:
        best_trend = self.best_trends(limit=1)
        best_format = self.best_formats(limit=1)
        best_style = self.best_styles(limit=1)
        best_angle = self.best_angles(limit=1)
        best_mood = self.best_visual_moods(limit=1)
        best_palette = self.best_palettes(limit=1)
        best_camera = self.best_camera_styles(limit=1)
        best_rhythm = self.best_rhythms(limit=1)

        return {
            "trend": best_trend[0]["name"] if best_trend else None,
            "content_type": best_format[0]["name"] if best_format else None,
            "style": best_style[0]["name"] if best_style else None,
            "angle": best_angle[0]["name"] if best_angle else None,
            "visual_mood": best_mood[0]["name"] if best_mood else None,
            "palette": best_palette[0]["name"] if best_palette else None,
            "camera_style": best_camera[0]["name"] if best_camera else None,
            "rhythm": best_rhythm[0]["name"] if best_rhythm else None,
        }


studio_memory = StudioMemory()
