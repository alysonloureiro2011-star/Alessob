from typing import Dict, List, Optional
import time

class SignalFusion:
    """
    Consolida sinais de múltiplas fontes (tendências externas, métricas internas,
    experimentos, memória de estúdio) em uma visão unificada.
    Fornece snapshots para world_model e cognitive_integrator.
    """

    def __init__(self):
        # armazenamento de sinais categorizados
        self.external_trends: List[Dict] = []
        self.instagram_metrics: List[Dict] = []
        self.experiment_results: List[Dict] = []
        self.timestamp = time.time()

        # definir máximo de registros para evitar crescimento infinito
        self.max_records = 200

    # ---------------------------------------------
    # Ingestão de sinais externos
    # ---------------------------------------------
    def add_external_trends(self, trends: List[Dict]) -> None:
        """
        Adiciona uma lista de sinais externos.
        Cada trend deve ser um dict com 'topic' e 'weight' ou 'score'.
        Ex.: {'topic': 'minimalismo', 'weight': 0.8}
        """
        for trend in trends:
            trend['timestamp'] = time.time()
            self.external_trends.append(trend)
        # manter o tamanho sob controle
        self.external_trends = self.external_trends[-self.max_records:]

    # ---------------------------------------------
    # Ingestão de métricas do Instagram
    # ---------------------------------------------
    def add_instagram_metrics(self, metrics: Dict) -> None:
        """
        Adiciona um conjunto de métricas internas (likes, comments, shares etc.).
        Usa o timestamp atual como marcador.
        """
        metrics['timestamp'] = time.time()
        self.instagram_metrics.append(metrics)
        self.instagram_metrics = self.instagram_metrics[-self.max_records:]

    # ---------------------------------------------
    # Ingestão de resultados de experimentos
    # ---------------------------------------------
    def add_experiment_result(self, result: Dict) -> None:
        """
        Adiciona resultado de um teste A/B ou experimento.
        Ex.: {'hypothesis': 'hook segredo', 'variant': 'conflito moral', 'performance': 0.82}
        """
        result['timestamp'] = time.time()
        self.experiment_results.append(result)
        self.experiment_results = self.experiment_results[-self.max_records:]

    # ---------------------------------------------
    # Snapshot consolidado
    # ---------------------------------------------
    def get_snapshot(self) -> Dict:
        """
        Retorna snapshot unificado com:
        - top_externals: tópicos externos ordenados por peso
        - recent_metrics: última métrica interna registrada
        - last_experiments: últimos resultados de experimentos
        """
        top_externals = sorted(
            self.external_trends,
            key=lambda x: x.get("weight", 0),
            reverse=True
        )[:10]

        recent_metrics = self.instagram_metrics[-1] if self.instagram_metrics else {}
        last_experiments = self.experiment_results[-5:] if self.experiment_results else []

        return {
            "timestamp": time.time(),
            "top_externals": top_externals,
            "recent_metrics": recent_metrics,
            "last_experiments": last_experiments
        }

    # ---------------------------------------------
    # Limpar sinais
    # ---------------------------------------------
    def clear_signals(self) -> None:
        """
        Limpa todos os registros. Útil para resetar estado ou após exportar dados.
        """
        self.external_trends.clear()
        self.instagram_metrics.clear()
        self.experiment_results.clear()

# Instância global (opcional)
signal_fusion: Optional[SignalFusion] = None

def install_signal_fusion(ace_runtime: Any) -> SignalFusion:
    """
    Instala o signal_fusion no runtime do ACE. Deve ser chamado no boot,
    antes do cognitive_integrator ler os snapshots.
    """
    global signal_fusion
    signal_fusion = SignalFusion()
    ace_runtime.signal_fusion = signal_fusion
    return signal_fusion
