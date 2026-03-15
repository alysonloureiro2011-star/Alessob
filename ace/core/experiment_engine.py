from typing import Dict, List, Tuple
import random

class ExperimentEngine:
    def __init__(self):
        # Lista de experimentos ativos
        self.active_experiments: List[Dict] = []
        self.results: List[Dict] = []

    def create_experiment(
        self,
        hypothesis_id: str,
        parameter: str,
        variants: List[str],
        sample_size: int
    ) -> Dict:
        """
        Define um experimento A/B ou multivariado.
        :param hypothesis_id: identificador da hipótese associada.
        :param parameter: o parâmetro sendo testado (ex.: 'hook', 'style').
        :param variants: lista de variações desse parâmetro.
        :param sample_size: quantas vezes cada variante deve ser testada.
        """
        exp = {
            "experiment_id": f"EXP-{random.randint(10000, 99999)}",
            "hypothesis_id": hypothesis_id,
            "parameter": parameter,
            "variants": variants,
            "sample_size": sample_size,
            "assignments": [],
            "completed": False
        }
        # preparar distribuições
        for variant in variants:
            for _ in range(sample_size):
                exp["assignments"].append({"variant": variant, "executed": False})
        random.shuffle(exp["assignments"])
        self.active_experiments.append(exp)
        return exp

    def assign_next_variant(self, experiment_id: str) -> Tuple[str, Dict]:
        """
        Escolhe a próxima variante a ser executada para um experimento.
        """
        exp = self._get_experiment(experiment_id)
        if not exp or exp["completed"]:
            return ("", {})
        for assignment in exp["assignments"]:
            if not assignment["executed"]:
                assignment["executed"] = True
                return (assignment["variant"], {"hypothesis_id": exp["hypothesis_id"], "parameter": exp["parameter"]})
        exp["completed"] = True
        return ("", {})

    def record_result(
        self,
        experiment_id: str,
        variant: str,
        performance: float,
        quality: float
    ) -> None:
        """
        Registra resultado de uma variação.
        """
        self.results.append({
            "experiment_id": experiment_id,
            "variant": variant,
            "performance": performance,
            "quality": quality
        })

    def conclude_experiment(self, experiment_id: str) -> Dict:
        """
        Analisa os resultados de um experimento, determina a melhor variante e gera conclusão.
        """
        relevant = [r for r in self.results if r["experiment_id"] == experiment_id]
        if not relevant:
            return {"experiment_id": experiment_id, "winner": None}
        # pontuação composta simples
        for r in relevant:
            r["score"] = r["performance"] * 0.6 + r["quality"] * 0.4
        sorted_results = sorted(relevant, key=lambda x: x["score"], reverse=True)
        best_variant = sorted_results[0]["variant"]
        # atualizar hipóteses, metas ou memória externa aqui (hooks para outros módulos)
        # ...
        return {
            "experiment_id": experiment_id,
            "winner": best_variant,
            "results": sorted_results
        }

    def _get_experiment(self, experiment_id: str) -> Dict:
        for exp in self.active_experiments:
            if exp["experiment_id"] == experiment_id:
                return exp
        return {}
