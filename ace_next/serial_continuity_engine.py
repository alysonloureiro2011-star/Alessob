from __future__ import annotations

from typing import Any, Dict, List

def build_serial_continuity(creative_plan: Dict[str, Any], recent_memory: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """
    Constrói um objeto de continuidade serial para preservar narrativa entre episódios.
    
    Args:
        creative_plan: O plano criativo atual.
        recent_memory: Lista de episódios recentes (últimos posts), se existirem.
        
    Returns:
        dict com chaves:
            - ok: bool (se o processo foi bem-sucedido)
            - next_episode_seed: str (sugestão de gancho para próximo episódio)
            - continuity_notes: str (resumo textual sobre ligações passadas)
            - hints: list (lista de sugestões de continuidade)
    """
    # Tratamentos defensivos
    recent_memory = recent_memory or []
    continuity_notes = []
    hints: List[str] = []

    # Exemplo simples: extrair ganchos anteriores e sugerir variações
    for memory in recent_memory[-3:]:
        seed = str(memory.get("topic_seed") or memory.get("headline") or "")
        if seed:
            continuity_notes.append(f"Revisite ou evolua o tema: {seed}")
            hints.append(seed)

    # Próximo episódio parte do último, se houver memória
    next_episode_seed = hints[-1] if hints else creative_plan.get("topic_seed") or creative_plan.get("headline")

    return {
        "ok": True,
        "next_episode_seed": next_episode_seed,
        "continuity_notes": "; ".join(continuity_notes),
        "hints": hints,
                            }
