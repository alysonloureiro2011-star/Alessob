from typing import Any, Dict, Optional
import time


class CycleGovernor:
    """
    Governa o ciclo de criação do ACE Ω. Decide quando iniciar ou pausar um ciclo
    com base em cooldown, resultados recentes e governança externa.
    """

    def __init__(self, ace_runtime: Any, cooldown_minutes: int = 45):
        self.ace = ace_runtime
        self.last_cycle_at: Optional[float] = None
        self.cooldown_seconds = cooldown_minutes * 60

    def _now(self) -> float:
        return time.time()

    def _in_cooldown(self) -> bool:
        if not self.last_cycle_at:
            return False
        return (self._now() - self.last_cycle_at) < self.cooldown_seconds

    def should_start_cycle(self) -> bool:
        """
        Retorna True se o ACE pode iniciar um novo ciclo.
        Considera cooldown e sinal de governança externa (por exemplo, saturação de temas).
        """
        if self._in_cooldown():
            return False

        # Checa se a governança externa libera um novo ciclo:
        # Caso exista um método ace_governance_allow_cycle no runtime
        allow = getattr(self.ace, "ace_governance_allow_cycle", None)
        if callable(allow):
            return bool(allow())
        return True

    def start_cycle(self) -> Dict[str, Any]:
        """
        Inicia um novo ciclo se permitido. Integra com o CognitiveIntegrator
        para obter a intenção do ciclo e passa para o executor soberano.
        """
        if not self.should_start_cycle():
            return {"ok": False, "reason": "cooldown_or_governance_block"}

        integrator = getattr(self.ace, "cognitive_integrator", None)
        if not integrator:
            return {"ok": False, "reason": "cognitive_integrator_missing"}

        # Obter intenção consolidada (trend, content_type, estilo, etc.)
        intent: Dict[str, Any] = integrator.get_cycle_intent()

        # Passar intenção para o executor soberano
        executor = getattr(self.ace, "executor_soberano", None)
        if executor:
            # Por simplicidade, assume-se que um método executar com intent existirá.
            # Pode ser adaptado conforme seu executor real.
            result = executor.enqueue_task_soberano(
                task_type=intent.get("content_type", "reel"),
                trend=intent.get("trend"),
                style=intent.get("style"),
                priority=intent.get("priority", 1.0),
            )
        else:
            result = {"ok": False, "reason": "executor_soberano_missing"}

        self.last_cycle_at = self._now()
        return {"ok": True, "intent": intent, "queue_result": result}


# Instância global (opcional)
cycle_governor: Optional[CycleGovernor] = None


def install_cycle_governor(ace_runtime: Any, cooldown_minutes: int = 45) -> CycleGovernor:
    """
    Instala o CycleGovernor no runtime do ACE. Deve ser chamado no boot.
    """
    global cycle_governor
    cycle_governor = CycleGovernor(ace_runtime, cooldown_minutes)
    ace_runtime.cycle_governor = cycle_governor
    return cycle_governor
