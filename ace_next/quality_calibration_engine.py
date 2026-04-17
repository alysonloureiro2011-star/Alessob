from __future__ import annotations

from typing import Any, Dict, List

class QualityCalibrationEngine:
    """
    Avalia e sugere ajustes no plano criativo.
    O foco é melhorar clareza, ritmo, hook e CTA para maximizar retenção.
    """

    def evaluate_plan(self, creative_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recebe o plano criativo e devolve recomendações.
        Examina tamanho do hook, corpo, CTA e valor percebido.

        Returns:
            dict contendo:
                ok: bool
                issues: list (problemas detectados)
                suggestions: list (sugestões de melhoria)
        """
        issues: List[str] = []
        suggestions: List[str] = []

        hook = str(creative_plan.get("hook", "")).strip()
        body = str(creative_plan.get("body", "")).strip()
        cta = str(creative_plan.get("cta", "")).strip()
        payoff = str(creative_plan.get("payoff", "")).strip()

        # Hook muito longo (> 12 palavras)
        if len(hook.split()) > 12:
            issues.append("Hook longo")
            suggestions.append("Reduza o hook para até 12 palavras e inclua curiosidade ou promessa clara.")

        # Corpo longo (> 60 palavras) sem micro-payoffs
        if len(body.split()) > 60:
            issues.append("Corpo extenso")
            suggestions.append("Quebre o corpo em micro-payoffs e varie o ritmo para manter a atenção.")

        # CTA fraco ou ausente
        if not cta or len(cta.split()) < 3:
            issues.append("CTA fraco")
            suggestions.append("Inclua um CTA claro (por exemplo, 'Salve e compartilhe se fizer sentido').")

        # Payoff sem valor percebido
        if not payoff or len(payoff.split()) < 5:
            issues.append("Valor percebido baixo")
            suggestions.append("Reforce o payoff destacando o benefício prático ou emocional ao público.")

        return {
            "ok": not issues,
            "issues": issues,
            "suggestions": suggestions,
        }
