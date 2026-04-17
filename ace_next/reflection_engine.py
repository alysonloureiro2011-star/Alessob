from __future__ import annotations

from typing import Any, Dict

class ReflectionEngine:
    """
    Motor de reflexão que gera insights a partir de métricas reais e recomendações.
    Pode ser estendido futuramente com algoritmos mais sofisticados.
    """

    def run(
        self,
        creative_plan: Dict[str, Any],
        real_metrics: Dict[str, Any] | None,
        recommendation_engine: Dict[str, Any] | None,
        attention_metrics: Dict[str, Any] | None,
    ) -> Dict[str, Any]:
        """
        Processa métricas e recomendações para sugerir ajustes no próximo ciclo.
        
        Args:
            creative_plan: O plano criativo utilizado.
            real_metrics: Métricas de performance real (likes, saves, share, etc.).
            recommendation_engine: Recomendações geradas pelo sistema.
            attention_metrics: Métricas de atenção extraídas da plataforma.
        
        Returns:
            dict com chaves:
                - ok: bool
                - insights: list (sugestões textuais para melhorar próximos posts)
                - focus_areas: list (áreas de prioridade, ex: 'hook', 'formato', 'CTA')
        """
        insights = []
        focus_areas = []

        if real_metrics:
            saves = real_metrics.get("save_rate")
            shares = real_metrics.get("share_rate")
            retention = real_metrics.get("retention")
            
            if saves and saves < 0.1:
                insights.append("Elevar o CTA para salvamento ou destacar valor prático.")
                focus_areas.append("cta")
            if shares and shares < 0.1:
                insights.append("Criar estímulos de compartilhamento no final do vídeo.")
                focus_areas.append("desfecho")
            if retention and retention < 0.5:
                insights.append("Revisar ritmo e reduzir trechos lentos.")
                focus_areas.append("ritmo")

        # Sugerir incorporar comentários das recomendações do próprio sistema
        if recommendation_engine:
            rec = recommendation_engine.get("recommended_action")
            if rec:
                insights.append(f"Sugestão do RecommendationEngine: {rec}")

        return {
            "ok": True,
            "insights": insights,
            "focus_areas": list(set(focus_areas)),
        }
