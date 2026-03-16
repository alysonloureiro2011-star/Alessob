# ==========================================================
# ACE Ω — LIVING MYTH ENGINE V1
# FASE 1 — NÚCLEO PLAUSÍVEL
# ==========================================================

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List

MYTH_MEMORY_PATH = "ace_data/living_myth_memory.json"

DEFAULT_MYTH_MEMORY = {
    "last_tension": None,
    "last_chapter_stage": None,
    "last_symbolic_anchor": None,
    "recent_tensions": [],
    "recent_symbols": [],
    "history": [],
    "updated_at": None,
}

TENSION_RULES = {
    "caos_vs_controle": [
        "disciplina",
        "foco",
        "rotina",
        "ordem",
        "controle",
        "organização",
        "produtividade",
        "consistência",
    ],
    "ansiedade_vs_paz": [
        "ansiedade",
        "pressa",
        "silêncio",
        "calma",
        "paz",
        "respirar",
        "mente",
        "emocional",
    ],
    "medo_vs_coragem": [
        "medo",
        "coragem",
        "ousadia",
        "ação",
        "arriscar",
        "bloqueio",
        "enfrentar",
    ],
    "escassez_vs_abundancia": [
        "escassez",
        "abundância",
        "riqueza",
        "prosperidade",
        "dinheiro",
        "valor",
        "crescimento",
    ],
    "estagnacao_vs_transformacao": [
        "estagnação",
        "transformação",
        "mudança",
        "evolução",
        "renascimento",
        "progresso",
        "potência",
    ],
    "vergonha_vs_autoridade": [
        "vergonha",
        "autoridade",
        "presença",
        "postura",
        "respeito",
        "imagem",
        "voz",
    ],
    "superficialidade_vs_significado": [
        "significado",
        "propósito",
        "essência",
        "verdade",
        "profundidade",
        "sentido",
    ],
    "mediocridade_vs_potencia": [
        "mediocridade",
        "potência",
        "excelência",
        "elite",
        "força",
        "capacidade",
        "nível",
    ],
}

SYMBOLIC_ANCHORS = {
    "caos_vs_controle": ["disciplina", "aço", "ritual", "eixo"],
    "ansiedade_vs_paz": ["silêncio", "respiração", "centro", "água"],
    "medo_vs_coragem": ["fogo", "passagem", "guerra", "lança"],
    "escassez_vs_abundancia": ["colheita", "ouro", "expansão", "semente"],
    "estagnacao_vs_transformacao": ["renascimento", "ponte", "ruptura", "metamorfose"],
    "vergonha_vs_autoridade": ["trono", "voz", "espelho", "presença"],
    "superficialidade_vs_significado": ["abismo", "essência", "núcleo", "templo"],
    "mediocridade_vs_potencia": ["forja", "potência", "ascensão", "coroa"],
}

CHAPTER_FLOW = ["abrir", "aprofundar", "resolver"]


def myth_now_iso() -> str:
    return datetime.now().isoformat()


def myth_safe_text(value: Any) -> str:
    return str(value or "").strip().lower()


def myth_ensure_memory_dir() -> None:
    folder = os.path.dirname(MYTH_MEMORY_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)


def myth_load_memory() -> Dict[str, Any]:
    try:
        if os.path.exists(MYTH_MEMORY_PATH):
            with open(MYTH_MEMORY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    merged = dict(DEFAULT_MYTH_MEMORY)
                    merged.update(data)
                    return merged
    except Exception:
        pass
    return dict(DEFAULT_MYTH_MEMORY)


def myth_save_memory(memory: Dict[str, Any]) -> None:
    try:
        myth_ensure_memory_dir()
        memory["updated_at"] = myth_now_iso()
        with open(MYTH_MEMORY_PATH, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def myth_detect_tension(trend: str) -> str:
    text = myth_safe_text(trend)

    best_tension = "estagnacao_vs_transformacao"
    best_score = -1

    for tension, keywords in TENSION_RULES.items():
        score = 0
        for keyword in keywords:
            if keyword in text:
                score += 1
        if score > best_score:
            best_score = score
            best_tension = tension

    return best_tension


def myth_choose_chapter_stage(memory: Dict[str, Any], tension: str) -> str:
    last_tension = memory.get("last_tension")
    last_stage = memory.get("last_chapter_stage")

    if last_tension != tension:
        return "abrir"

    if last_stage == "abrir":
        return "aprofundar"

    if last_stage == "aprofundar":
        return "resolver"

    return "abrir"


def myth_choose_symbolic_anchor(tension: str, memory: Dict[str, Any]) -> str:
    anchors = SYMBOLIC_ANCHORS.get(tension, ["núcleo"])
    recent_symbols = memory.get("recent_symbols", []) or []

    for anchor in anchors:
        if anchor not in recent_symbols[-2:]:
            return anchor

    return anchors[0]


def myth_build_direction(trend: str, tension: str, chapter_stage: str, symbolic_anchor: str) -> str:
    if chapter_stage == "abrir":
        return (
            f"Abrir a tensão '{tension}' a partir do tema '{trend}', "
            f"usando o símbolo '{symbolic_anchor}' como eixo narrativo."
        )

    if chapter_stage == "aprofundar":
        return (
            f"Aprofundar a tensão '{tension}' conectando o tema '{trend}' "
            f"ao símbolo '{symbolic_anchor}', elevando conflito e significado."
        )

    return (
        f"Resolver a tensão '{tension}' a partir do tema '{trend}', "
        f"transformando o símbolo '{symbolic_anchor}' em síntese, clareza e direção."
    )


def myth_choose_cta_mode(chapter_stage: str) -> str:
    if chapter_stage == "abrir":
        return "reflexao"

    if chapter_stage == "aprofundar":
        return "identificacao"

    return "movimento"


def myth_score(tension: str, chapter_stage: str) -> float:
    base = 0.60

    if tension in ("caos_vs_controle", "medo_vs_coragem", "mediocridade_vs_potencia"):
        base += 0.12

    if chapter_stage == "aprofundar":
        base += 0.08
    elif chapter_stage == "resolver":
        base += 0.05

    return round(min(base, 0.95), 2)


def myth_trim_history(items: List[Any], max_size: int = 12) -> List[Any]:
    return items[-max_size:]


def myth_update_memory(
    memory: Dict[str, Any],
    trend: str,
    tension: str,
    chapter_stage: str,
    symbolic_anchor: str,
    direction: str,
) -> Dict[str, Any]:
    memory["last_tension"] = tension
    memory["last_chapter_stage"] = chapter_stage
    memory["last_symbolic_anchor"] = symbolic_anchor

    recent_tensions = memory.get("recent_tensions", []) or []
    recent_symbols = memory.get("recent_symbols", []) or []
    history = memory.get("history", []) or []

    recent_tensions.append(tension)
    recent_symbols.append(symbolic_anchor)
    history.append({
        "trend": trend,
        "tension": tension,
        "chapter_stage": chapter_stage,
        "symbolic_anchor": symbolic_anchor,
        "direction": direction,
        "at": myth_now_iso(),
    })

    memory["recent_tensions"] = myth_trim_history(recent_tensions, max_size=8)
    memory["recent_symbols"] = myth_trim_history(recent_symbols, max_size=8)
    memory["history"] = myth_trim_history(history, max_size=12)

    return memory


def myth_run_cycle(trend: str, memory: Dict[str, Any] | None = None) -> Dict[str, Any]:
    trend = str(trend or "").strip() or "transformação pessoal"

    if memory is None:
        memory = myth_load_memory()

    tension = myth_detect_tension(trend)
    chapter_stage = myth_choose_chapter_stage(memory, tension)
    symbolic_anchor = myth_choose_symbolic_anchor(tension, memory)
    direction = myth_build_direction(trend, tension, chapter_stage, symbolic_anchor)
    cta_mode = myth_choose_cta_mode(chapter_stage)
    score = myth_score(tension, chapter_stage)

    result = {
        "ok": True,
        "trend": trend,
        "dominant_tension": tension,
        "chapter_stage": chapter_stage,
        "symbolic_anchor": symbolic_anchor,
        "narrative_direction": direction,
        "cta_mode": cta_mode,
        "myth_score": score,
        "memory_snapshot": {
            "last_tension": memory.get("last_tension"),
            "last_chapter_stage": memory.get("last_chapter_stage"),
            "last_symbolic_anchor": memory.get("last_symbolic_anchor"),
        },
    }

    updated_memory = myth_update_memory(
        memory=memory,
        trend=trend,
        tension=tension,
        chapter_stage=chapter_stage,
        symbolic_anchor=symbolic_anchor,
        direction=direction,
    )
    myth_save_memory(updated_memory)

    return result


def myth_debug_example() -> Dict[str, Any]:
    return myth_run_cycle("disciplina emocional")
