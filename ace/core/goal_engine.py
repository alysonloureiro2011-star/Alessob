from typing import Dict, Optional


class GoalEngine:

    def __init__(self):
        self.goals = {
            "authority": 1.0,
            "retention": 1.0,
            "saves": 1.0,
            "shares": 1.0,
            "growth": 1.0,
            "quality": 1.2,
            "novelty": 0.9,
            "consistency": 1.1,
        }

        self.history = []
        self.max_history = 300

    # --------------------------------------------------
    # definir peso manual
    # --------------------------------------------------

    def set_goal_weight(self, goal_name: str, weight: float) -> None:
        if goal_name in self.goals:
            self.goals[goal_name] = max(0.0, float(weight))

    # --------------------------------------------------
    # snapshot atual
    # --------------------------------------------------

    def current_goals(self) -> Dict:
        return {
            "goals": dict(self.goals)
        }

    # --------------------------------------------------
    # registrar resultado do ciclo
    # --------------------------------------------------

    def register_cycle(
        self,
        performance_score: float = 0.0,
        quality_score: float = 0.0,
        retention_score: float = 0.0,
        saves_score: float = 0.0,
        shares_score: float = 0.0,
        growth_score: float = 0.0,
        novelty_score: float = 0.0,
        consistency_score: float = 0.0,
        authority_score: float = 0.0,
    ) -> Dict:

        cycle = {
            "performance_score": float(performance_score),
            "quality_score": float(quality_score),
            "retention_score": float(retention_score),
            "saves_score": float(saves_score),
            "shares_score": float(shares_score),
            "growth_score": float(growth_score),
            "novelty_score": float(novelty_score),
            "consistency_score": float(consistency_score),
            "authority_score": float(authority_score),
        }

        self.history.append(cycle)

        if len(self.history) > self.max_history:
            self.history.pop(0)

        return cycle

    # --------------------------------------------------
    # meta que mais precisa de atenção
    # --------------------------------------------------

    def weakest_goal(self) -> Optional[str]:
        if not self.history:
            return None

        recent = self.history[-10:]

        averages = {
            "authority": sum(x["authority_score"] for x in recent) / len(recent),
            "retention": sum(x["retention_score"] for x in recent) / len(recent),
            "saves": sum(x["saves_score"] for x in recent) / len(recent),
            "shares": sum(x["shares_score"] for x in recent) / len(recent),
            "growth": sum(x["growth_score"] for x in recent) / len(recent),
            "quality": sum(x["quality_score"] for x in recent) / len(recent),
            "novelty": sum(x["novelty_score"] for x in recent) / len(recent),
            "consistency": sum(x["consistency_score"] for x in recent) / len(recent),
        }

        weakest = min(
            averages.keys(),
            key=lambda g: averages[g] * self.goals.get(g, 1.0)
        )

        return weakest

    # --------------------------------------------------
    # meta dominante do momento
    # --------------------------------------------------

    def dominant_goal(self) -> Optional[str]:
        if not self.goals:
            return None

        return max(self.goals.keys(), key=lambda g: self.goals[g])

    # --------------------------------------------------
    # tensão estratégica
    # --------------------------------------------------

    def strategic_tension(self) -> Dict:
        return {
            "quality_vs_growth": round(self.goals["quality"] - self.goals["growth"], 4),
            "novelty_vs_consistency": round(self.goals["novelty"] - self.goals["consistency"], 4),
            "retention_vs_shares": round(self.goals["retention"] - self.goals["shares"], 4),
            "authority_vs_saves": round(self.goals["authority"] - self.goals["saves"], 4),
        }

    # --------------------------------------------------
    # recomendação do próximo ciclo
    # --------------------------------------------------

    def recommend_focus(self) -> Dict:
        weak = self.weakest_goal()
        dominant = self.dominant_goal()
        tension = self.strategic_tension()

        if weak == "retention":
            recommendation = {
                "content_type": "reel",
                "style_bias": "curiosidade",
                "intensity_bias": "forte",
                "creative_bias": "close + hook
