from typing import Any, Dict


class CognitiveIntegrator:
    """
    Consolida todos os sinais cognitivos (world model, goal engine, hypothesis engine,
    performance brain, studio memory, meta-cognition) e devolve uma única
    intenção de ciclo.
    """

    def __init__(self, ace_runtime: Any):
        self.ace = ace_runtime

    def _get_module(self, name: str):
        return getattr(self.ace, name, None)

    def get_cycle_intent(self) -> Dict[str, Any]:
        """
        Gera uma intenção de ciclo unificada, com prioridade, trend, formato, estilo, etc.
        """
        # Coleta de dados dos módulos
        world_model = self._get_module("world_model")
        goal_engine = self._get_module("goal_engine")
        hypothesis_engine = self._get_module("hypothesis_engine")
        performance_brain = self._get_module("performance_brain")
        studio_memory = self._get_module("studio_memory")

        # 1. Identificar trend dominante/emergente
        trend = None
        if world_model:
            snapshot = world_model.world_snapshot()
            # escolher dominant trends, caso existam
            trends = snapshot.get("dominant_trends") or snapshot.get("emerging_trends")
            if trends:
                trend = trends[0]

        # 2. Verificar melhor formato segundo performance_brain
        content_type = "reel"
        if performance_brain:
            top_formats = performance_brain.top_formats(limit=1)
            if top_formats:
                content_type = top_formats[0]["name"]

        # 3. Escolher estilo e ângulo a partir do studio_memory e hypothesis_engine
        style = "autoridade"
        angle = "choque"
        if studio_memory:
            best_styles = studio_memory.best_styles(limit=1)
            if best_styles:
                style = best_styles[0]["name"]
        if hypothesis_engine and hasattr(hypothesis_engine, "best_hypotheses"):
            best_hyp = hypothesis_engine.best_hypotheses()
            if best_hyp:
                angle = best_hyp[0]["angle"]

        # 4. Ajustar prioridade com base no goal_engine
        priority = 1.0
        if goal_engine and hasattr(goal_engine, "current_goals"):
            goals = goal_engine.current_goals()
            # exemplo: dar mais peso se autoridade está fraca
            # (peso maior = prioridade menor)
            weakest = goal_engine.weakest_goal() if hasattr(goal_engine, "weakest_goal") else None
            if weakest == "authority":
                priority = 1.2
            elif weakest == "retention":
                priority = 1.1

        return {
            "trend": trend or "disciplina e prosperidade",
            "content_type": content_type,
            "style": style,
            "angle": angle,
            "priority": priority
        }


# Instância global (opcional)
cognitive_integrator: CognitiveIntegrator = None


def install_cognitive_integrator(ace_runtime: Any) -> CognitiveIntegrator:
    """
    Instala o integrador cognitivo no runtime do ACE. Deve ser chamado no boot.
    """
    global cognitive_integrator
    cognitive_integrator = CognitiveIntegrator(ace_runtime)
    ace_runtime.cognitive_integrator = cognitive_integrator
    return cognitive_integrator
