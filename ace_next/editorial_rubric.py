from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any

from .editorial_examples import examples_context
from .editorial_policy import detect_forbidden_patterns, detect_rejection_flags, lexicon_hits, normalize_text
from .editorial_staging_hardener import FORMAT_BUDGETS


@dataclass
class EditorialQAResult:
    approved: bool
    final_score: int
    minimum_score: int
    breakdown: dict[str, int]
    reasons: list[str]
    flags: list[str]
    approved_example_ids: list[str]
    rejected_example_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _bounded(score: float) -> int:
    return max(0, min(int(round(score)), 10))


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _normalize_format(value: Any) -> str:
    normalized = _clean_text(value).lower()
    if normalized in {"story", "stories"}:
        return "story"
    if normalized in {"carousel", "image"}:
        return normalized
    return "image"


def _length_score(text: str, *, minimum: int, ideal: int, hard_max: int) -> int:
    length = len(_clean_text(text))
    if length == 0:
        return 0
    if length < minimum:
        return _bounded(4 + (length / max(minimum, 1)) * 3.0)
    if length <= ideal:
        return 9
    if length <= hard_max:
        overflow = max(1, hard_max - ideal)
        penalty = ((length - ideal) / overflow) * 2.0
        return _bounded(9 - penalty)
    return 5


def _support_score(points: list[str], *, target_max: int) -> int:
    count = len([p for p in points if _clean_text(p)])
    if count == 0:
        return 4
    if count <= target_max:
        return 9
    if count == target_max + 1:
        return 7
    return 5


def _contains_any(text: str, terms: list[str]) -> bool:
    lowered = _clean_text(text).lower()
    return any(term in lowered for term in terms)


def evaluate_editorial_quality(plan: dict[str, Any]) -> EditorialQAResult:
    plan = dict(plan or {})

    format_name = _normalize_format(
        plan.get("publish_format_now")
        or plan.get("strategic_target_format")
        or plan.get("format_recommendation")
    )
    budgets = FORMAT_BUDGETS[format_name]

    headline = _clean_text(plan.get("headline"))
    hook = _clean_text(plan.get("hook"))
    body = _clean_text(plan.get("body"))
    cta = _clean_text(plan.get("cta"))
    support_points = [_clean_text(item) for item in _safe_list(plan.get("support_points")) if _clean_text(item)]
    hashtags = _safe_list(plan.get("hashtags"))
    topic = _clean_text(plan.get("topic_seed") or plan.get("trend_input"))

    full_text = " ".join([headline, hook, body, cta] + support_points)
    normalized = normalize_text(full_text)
    pattern_hits = detect_forbidden_patterns(full_text)
    policy_flags = detect_rejection_flags(headline=headline, hook=hook, body=body, cta=cta)
    lexicon = lexicon_hits(full_text)
    ex = examples_context(topic)

    headline_score = _length_score(
        headline,
        minimum=18,
        ideal=budgets["headline_chars"] - 8,
        hard_max=budgets["headline_chars"],
    )
    hook_score = _length_score(
        hook,
        minimum=28,
        ideal=budgets["hook_chars"] - 10,
        hard_max=budgets["hook_chars"],
    )
    body_score = _length_score(
        body,
        minimum=48,
        ideal=budgets["body_chars"] - 12,
        hard_max=budgets["body_chars"],
    )
    cta_visible_score = _length_score(
        cta,
        minimum=10,
        ideal=max(18, budgets["cta_chars"] - 8),
        hard_max=budgets["cta_chars"],
    )
    support_visible_score = _support_score(
        support_points,
        target_max=budgets["support_points_max"],
    )

    unique_words = len(set(normalized.split()))
    semantic_density = _bounded(
        5
        + (2 if unique_words >= 18 else 0)
        + (1 if len(lexicon) >= 3 else 0)
        + (1 if len(body) >= 60 else 0)
    )

    authority = _bounded(
        5
        + (2 if _contains_any(full_text, ["critério", "criterio", "processo", "execução", "execucao", "direção", "direcao", "leitura"]) else 0)
        + (1 if "!" not in full_text else 0)
        + (1 if len(body.split(". ")) >= 2 else 0)
    )

    perceived_value = _bounded(
        (
            body_score
            + support_visible_score
            + (1 if len(lexicon) >= 2 else 0)
            + (1 if len(hashtags) >= 3 else 0)
        ) / 1.2
    )

    narrative_tension = _bounded(
        5
        + (2 if _contains_any(" ".join([headline, hook, body]), ["erro", "travamento", "silencioso", "na prática", "na pratica", "verdade", "armadilha", "ilusão", "ilusao"]) else 0)
        + (1 if _contains_any(hook, ["por que", "como", "o que", "antes"]) else 0)
        + (1 if len(hook) >= 40 else 0)
    )

    naturalism = _bounded(
        5
        + (2 if not pattern_hits else 0)
        + (1 if not _contains_any(full_text, ["você precisa", "voce precisa", "isso muda tudo", "acredite em você", "acredite em voce"]) else 0)
        + (1 if len(body.split(". ")) >= 2 else 0)
    )

    anti_generic = _bounded(
        5
        + (2 if not _contains_any(full_text, ["segredo", "ninguém te conta", "ninguem te conta", "isso muda tudo", "mude sua vida"]) else 0)
        + (1 if len(lexicon) >= 2 else 0)
        + (1 if unique_words >= 18 else 0)
    )

    anti_commodity = _bounded(
        5
        + (2 if not pattern_hits else 0)
        + (1 if not _contains_any(cta, ["comente aqui", "corre", "chama na dm", "compra agora", "agora"]) else 0)
        + (1 if _contains_any(cta, ["salve", "envie", "compartilhe", "releia"]) else 0)
    )

    clarity = _bounded(
        (
            headline_score
            + hook_score
            + body_score
            + cta_visible_score
            + support_visible_score
        ) / 5.0
    )

    breakdown = {
        "headline": headline_score,
        "hook": hook_score,
        "clarity": clarity,
        "semantic_density": semantic_density,
        "authority": authority,
        "perceived_value": perceived_value,
        "narrative_tension": narrative_tension,
        "naturalism": naturalism,
        "anti_generic": anti_generic,
        "anti_commodity": anti_commodity,
        "cta": cta_visible_score,
    }

    reasons: list[str] = []

    if len(headline) < 18:
        reasons.append("headline ainda curta para sustentar autoridade")
    if len(headline) > budgets["headline_chars"]:
        reasons.append("headline acima do budget visual do formato")
    if len(hook) < 28:
        reasons.append("hook ainda curta para criar tensão suficiente")
    if len(hook) > budgets["hook_chars"]:
        reasons.append("hook acima do budget visual do formato")
    if len(body) < 48:
        reasons.append("body ainda curta para sustentar valor percebido")
    if len(body) > budgets["body_chars"]:
        reasons.append("body acima do budget visual do formato")
    if len(support_points) > budgets["support_points_max"]:
        reasons.append("support points acima do limite visível do formato")
    if pattern_hits:
        reasons.append("foram detectados padrões proibidos de linguagem")
    if not lexicon:
        reasons.append("texto com poucos sinais do léxico de marca")
    if _contains_any(cta, ["comente aqui", "corre", "chama na dm", "compra agora"]):
        reasons.append("cta ainda vulgar para padrão premium")
    if _contains_any(full_text, ["segredo", "ninguém te conta", "ninguem te conta", "isso muda tudo", "mude sua vida"]):
        reasons.append("texto ainda com traço commodity")

    flags = list(dict.fromkeys(policy_flags + (["forbidden_patterns"] if pattern_hits else [])))

    final_score = int(round(sum(breakdown.values()) / len(breakdown) * 10))
    final_score -= min(len(flags) * 5, 20)
    minimum_score = int(os.environ.get("ACE_MIN_EDITORIAL_SCORE", "74"))
    final_score = max(0, min(final_score, 100))

    approved = (
        final_score >= minimum_score
        and breakdown["headline"] >= 7
        and breakdown["hook"] >= 7
        and breakdown["clarity"] >= 7
        and breakdown["naturalism"] >= 7
        and breakdown["anti_generic"] >= 7
        and breakdown["anti_commodity"] >= 7
    )

    if approved and not reasons:
        reasons.append("editorial dentro do mínimo soberano para laboratório ou staging")

    return EditorialQAResult(
        approved=approved,
        final_score=final_score,
        minimum_score=minimum_score,
        breakdown=breakdown,
        reasons=reasons,
        flags=flags,
        approved_example_ids=ex["approved_ids"],
        rejected_example_ids=ex["rejected_ids"],
    )
