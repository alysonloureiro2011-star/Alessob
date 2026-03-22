from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any

from .editorial_examples import examples_context
from .editorial_policy import detect_forbidden_patterns, detect_rejection_flags, lexicon_hits, normalize_text


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


def _bounded(score: int) -> int:
    return max(0, min(score, 10))


def evaluate_editorial_quality(plan: dict[str, Any]) -> EditorialQAResult:
    headline = (plan.get("headline") or "").strip()
    hook = (plan.get("hook") or "").strip()
    body = (plan.get("body") or "").strip()
    cta = (plan.get("cta") or "").strip()
    support_points = plan.get("support_points") or []
    hashtags = plan.get("hashtags") or []
    topic = (plan.get("topic_seed") or plan.get("trend_input") or "").strip()

    full_text = " ".join([headline, hook, body, cta] + list(support_points))
    normalized = normalize_text(full_text)
    pattern_hits = detect_forbidden_patterns(full_text)
    policy_flags = detect_rejection_flags(headline=headline, hook=hook, body=body, cta=cta)
    lexicon = lexicon_hits(full_text)
    ex = examples_context(topic)

    breakdown = {
        "headline": _bounded(5 + (2 if len(headline) >= 28 else 0) + (1 if ":" not in headline else 0) + (1 if len(headline.split()) >= 6 else 0)),
        "hook": _bounded(5 + (2 if len(hook) >= 90 else 0) + (1 if "?" not in hook else 0) + (1 if len(hook.split()) >= 14 else 0)),
        "clarity": _bounded(5 + (2 if len(body) >= 140 else 0) + (1 if len(support_points) >= 3 else 0) + (1 if len(body.split(". ")) >= 3 else 0)),
        "semantic_density": _bounded(4 + min(len(lexicon), 4) + (1 if len(set(normalized.split())) >= 24 else 0)),
        "authority": _bounded(4 + (2 if any(term in normalized for term in ["critério", "processo", "execução", "direção", "leitura"]) else 0) + (1 if "!" not in full_text else 0) + (1 if len(body) >= 160 else 0)),
        "perceived_value": _bounded(4 + (2 if len(body) >= 160 else 0) + (1 if len(support_points) >= 3 else 0) + (1 if len(hashtags) >= 5 else 0)),
        "narrative_tension": _bounded(4 + (2 if any(term in normalized for term in ["erro", "travamento", "silencioso", "quase sempre", "na prática"]) else 0) + (1 if len(hook) >= 85 else 0)),
        "naturalism": _bounded(5 + (2 if not pattern_hits else 0) + (1 if "você precisa" not in normalized else 0) + (1 if len(body.split(". ")) >= 3 else 0)),
        "anti_generic": _bounded(4 + min(len(lexicon), 3) + (1 if not any(term in normalized for term in ["acredite", "sonhe", "mude sua vida"]) else 0) + (1 if len(set(normalized.split())) >= 24 else 0)),
        "anti_commodity": _bounded(4 + (2 if not pattern_hits else 0) + (1 if "viral" not in normalized else 0) + (1 if cta.lower().startswith("salve") else 0)),
        "cta": _bounded(4 + (2 if len(cta) >= 55 else 0) + (1 if any(term in cta.lower() for term in ["salve", "envie", "compartilhe", "releia"]) else 0) + (1 if "agora" not in cta.lower() else 0)),
    }

    reasons: list[str] = []
    if len(headline) < 24:
        reasons.append("headline ainda curta para padrão soberano")
    if len(hook) < 70:
        reasons.append("hook ainda fraco para tensão editorial")
    if len(body) < 120:
        reasons.append("body ainda curto para sustentar valor percebido")
    if len(support_points) < 3:
        reasons.append("faltam pontos de apoio suficientes")
    if pattern_hits:
        reasons.append("foram detectados padrões proibidos de linguagem")
    if not lexicon:
        reasons.append("texto com poucos sinais do léxico de marca")

    flags = list(dict.fromkeys(policy_flags + (["forbidden_patterns"] if pattern_hits else [])))

    final_score = int(round(sum(breakdown.values()) / len(breakdown) * 10))
    final_score -= min(len(flags) * 5, 20)
    minimum_score = int(os.environ.get("ACE_MIN_EDITORIAL_SCORE", "74"))
    final_score = max(0, min(final_score, 100))

    approved = (
        final_score >= minimum_score
        and breakdown["headline"] >= 7
        and breakdown["hook"] >= 7
        and breakdown["naturalism"] >= 7
        and breakdown["anti_generic"] >= 7
        and breakdown["anti_commodity"] >= 7
    )

    if approved and not reasons:
        reasons.append("editorial dentro do mínimo aceitável para a fase atual")

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
