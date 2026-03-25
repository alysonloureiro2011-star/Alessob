from __future__ import annotations

import re
from typing import Any

DEFAULT_SERIES_NAME = "Liberta a Verdade"


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize(value: Any) -> str:
    return _clean(value).lower()


def _keywords(value: Any) -> list[str]:
    text = _normalize(value)
    words = re.findall(r"[a-zà-ÿ0-9]{3,}", text)
    stopwords = {
        "para", "com", "sem", "isso", "essa", "esse", "como", "mais", "menos", "sobre",
        "uma", "uns", "umas", "por", "que", "das", "dos", "nas", "nos", "the", "and",
    }
    unique: list[str] = []
    for word in words:
        if word in stopwords:
            continue
        if word not in unique:
            unique.append(word)
    return unique[:10]


def _extract_recent_candidates(memory_context: dict[str, Any]) -> list[dict[str, Any]]:
    memory_context = _safe_dict(memory_context)
    candidates: list[dict[str, Any]] = []

    direct_lists = [
        "ace_content_history",
        "ace_candidate_posts",
        "recent_posts",
        "recent_content",
        "episodes",
    ]
    for key in direct_lists:
        for item in _safe_list(memory_context.get(key)):
            if isinstance(item, dict):
                candidates.append(item)

    episodic = _safe_dict(memory_context.get("episodic_performance_memory"))
    for key in ["episodes", "records", "items"]:
        for item in _safe_list(episodic.get(key)):
            if isinstance(item, dict):
                candidates.append(item)

    registry = _safe_dict(memory_context.get("experiment_registry"))
    for key in ["experiments", "records", "items"]:
        for item in _safe_list(registry.get(key)):
            if isinstance(item, dict):
                candidates.append(item)

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates:
        identity = _clean(
            item.get("content_hash")
            or item.get("id")
            or item.get("title")
            or item.get("headline")
            or item.get("hook")
        )
        if identity and identity not in seen:
            seen.add(identity)
            deduped.append(item)
    return deduped[:20]


def _keyword_overlap(a: list[str], b: list[str]) -> int:
    return len(set(a) & set(b))


def _best_recent_match(topic_seed: str, candidates: list[dict[str, Any]]) -> tuple[dict[str, Any], int]:
    topic_keys = _keywords(topic_seed)
    best_item: dict[str, Any] = {}
    best_score = 0

    for item in candidates:
        joined = " ".join(
            [
                _clean(item.get("topic_seed")),
                _clean(item.get("trend")),
                _clean(item.get("headline")),
                _clean(item.get("hook")),
                _clean(item.get("problem")),
                _clean(item.get("angle")),
            ]
        )
        score = _keyword_overlap(topic_keys, _keywords(joined))
        if _clean(item.get("series_name")):
            score += 1
        if score > best_score:
            best_score = score
            best_item = item

    return best_item, best_score


def _episode_index_hint(best_item: dict[str, Any], sequel_candidate: bool) -> int:
    raw = best_item.get("episode_index_hint") or best_item.get("episode_index") or best_item.get("episode")
    try:
        base = int(raw)
    except Exception:
        base = 1
    if sequel_candidate:
        return max(2, base + 1)
    return max(1, base)


def _next_episode_seed(topic_seed: str, best_item: dict[str, Any], sequel_candidate: bool) -> str:
    keys = _keywords(topic_seed)
    primary = keys[0] if len(keys) > 0 else "clareza"
    secondary = keys[1] if len(keys) > 1 else "disciplina"

    carry_problem = _clean(best_item.get("problem"))
    if sequel_candidate and carry_problem:
        return f"O custo que aparece depois de buscar {primary} sem {secondary}"
    if sequel_candidate:
        return f"O próximo erro comum em {primary} quando {secondary} ainda falta"
    return f"A continuação natural de {primary} com mais {secondary}"


def build_serial_continuity_engine_v1(
    *,
    topic_seed: str,
    hook: str,
    angle: str,
    sequel_potential: str = "medium",
    memory_context: dict[str, Any] | None = None,
    series_name: str | None = None,
) -> dict[str, Any]:
    memory_context = _safe_dict(memory_context)
    candidates = _extract_recent_candidates(memory_context)
    best_item, overlap_score = _best_recent_match(topic_seed, candidates)

    sequel_candidate = sequel_potential in {"medium", "high"} or overlap_score >= 2 or bool(best_item)
    resolved_series_name = (
        _clean(series_name)
        or _clean(best_item.get("series_name"))
        or DEFAULT_SERIES_NAME
    )
    episode_index_hint = _episode_index_hint(best_item, sequel_candidate)

    carryover_hook = _clean(best_item.get("hook") or best_item.get("headline"))
    carryover_problem = _clean(best_item.get("problem") or best_item.get("angle"))
    carryover_payoff = _clean(best_item.get("payoff"))

    if best_item:
        continuity_reason = "há continuidade plausível com peça recente já registrada"
        source_mode = "memory_informed"
    elif sequel_candidate:
        continuity_reason = "o tema tem potencial serial mesmo sem memória forte ainda"
        source_mode = "conservative_fallback"
    else:
        continuity_reason = "o tema atual pode viver sozinho sem exigir continuação imediata"
        source_mode = "conservative_fallback"

    return {
        "ok": True,
        "series_name": resolved_series_name,
        "episode_index_hint": episode_index_hint,
        "sequel_candidate": bool(sequel_candidate),
        "next_episode_seed": _next_episode_seed(topic_seed, best_item, sequel_candidate),
        "continuity_reason": continuity_reason,
        "carryover_hook": carryover_hook,
        "carryover_problem": carryover_problem,
        "carryover_payoff": carryover_payoff,
        "continuity_confidence": "high" if overlap_score >= 3 else "medium" if sequel_candidate else "low",
        "source_mode": source_mode,
        "continuity_signals": {
            "recent_match_found": bool(best_item),
            "keyword_overlap": overlap_score,
            "sequel_potential": sequel_potential,
            "recent_series_name": _clean(best_item.get("series_name")),
            "recent_title": _clean(best_item.get("headline") or best_item.get("title")),
        },
    }


def serial_continuity_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "example_memory_informed": build_serial_continuity_engine_v1(
            topic_seed="clareza, disciplina e direção",
            hook="O problema raramente é falta de esforço.",
            angle="clareza precisa virar eixo",
            sequel_potential="high",
            memory_context={
                "ace_content_history": [
                    {
                        "series_name": "Liberta a Verdade",
                        "headline": "Sem disciplina, clareza perde força antes de virar resultado.",
                        "hook": "O travamento quase sempre nasce da falta de eixo.",
                        "problem": "clareza sem disciplina perde continuidade",
                        "payoff": "execução ganha direção",
                        "episode_index_hint": 2,
                    }
                ]
            },
        ),
        "example_fallback": build_serial_continuity_engine_v1(
            topic_seed="foco e constância",
            hook="Intenção não sustenta consistência sozinha.",
            angle="foco exige estrutura",
            sequel_potential="medium",
            memory_context={},
        ),
    }
