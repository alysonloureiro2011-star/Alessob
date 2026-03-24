from __future__ import annotations

from typing import Any

from .brand_ontology import get_brand_ontology


def resolve_pattern_interrupt_policy(
    format_type: str,
    hook: str,
    headline: str,
    body: str,
) -> dict[str, Any]:
    ontology = get_brand_ontology()
    combined = " ".join([hook or "", headline or "", body or ""]).lower()
    format_type = (format_type or "image").strip().lower()

    banned = []
    for pattern in ontology.get("forbidden_patterns", []):
        if str(pattern).lower() in combined:
            banned.append(pattern)

    if any(term in combined for term in ["antes que seja tarde", "última chance", "ninguém te conta"]):
        banned.append("manipulative_interrupt")

    if banned:
        return {
            "ok": True,
            "allowed": False,
            "interrupt_type": "blocked",
            "opening_strategy": "none",
            "semantic_shift": "none",
            "ethics_ok": False,
            "reasons": [
                "a abertura usa interrupção de padrão de forma antiética ou apelativa",
            ]
            + [f"bloqueado_por:{item}" for item in banned],
        }

    if any(term in combined for term in ["não é", "raramente", "quase sempre", "o erro não", "muita gente chama"]):
        interrupt_type = "misconception_flip"
        opening_strategy = "abrir quebrando a leitura comum do problema"
        semantic_shift = "trocar percepção superficial por leitura estrutural"
    elif any(term in combined for term in ["sem ", "custo", "silencioso", "desgaste", "travamento"]):
        interrupt_type = "hidden_cost"
        opening_strategy = "abrir com custo oculto ou efeito silencioso"
        semantic_shift = "mostrar o dano invisível do padrão atual"
    elif format_type == "reel":
        interrupt_type = "motion_hook_ready"
        opening_strategy = "primeira frase curta com contraste forte e continuação imediata"
        semantic_shift = "parar o scroll com tensão útil"
    else:
        interrupt_type = "semantic_contrast"
        opening_strategy = "abrir com contraste direto e linguagem limpa"
        semantic_shift = "mudar a leitura sem usar apelo barato"

    return {
        "ok": True,
        "allowed": True,
        "interrupt_type": interrupt_type,
        "opening_strategy": opening_strategy,
        "semantic_shift": semantic_shift,
        "ethics_ok": True,
        "reasons": [
            "quebra de padrão baseada em contraste semântico, não em manipulação",
            "abertura compatível com a política ética da marca",
        ],
    }
