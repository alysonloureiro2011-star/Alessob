from __future__ import annotations

import re
import unicodedata
from typing import Any

from .brand_lexicon import get_brand_lexicon, scan_brand_alignment


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize(value: Any) -> str:
    raw = _clean(value).lower()
    return "".join(
        char for char in unicodedata.normalize("NFKD", raw)
        if not unicodedata.combining(char)
    )


def _replace_weak_patterns(text: str) -> str:
    replacements = {
        "mude sua vida": "mude sua forma de decidir",
        "muda sua vida": "muda sua forma de decidir",
        "segredo": "ponto cego",
        "acredite em você": "organize melhor sua leitura",
        "acredite em voce": "organize melhor sua leitura",
        "ninguém te conta": "quase nunca é dito com clareza",
        "ninguem te conta": "quase nunca é dito com clareza",
        "isso muda tudo": "isso muda a leitura do problema",
        "viral": "forte",
        "imperdível": "relevante",
        "imperdivel": "relevante",
    }
    result = _clean(text)
    normalized = _normalize(result)
    for weak, strong in replacements.items():
        if weak in normalized:
            result = re.sub(weak, strong, result, flags=re.IGNORECASE)
    return _clean(result)


def _first_nonempty(*values: Any, fallback: str = "") -> str:
    for value in values:
        cleaned = _clean(value)
        if cleaned:
            return cleaned
    return fallback


def _truncate(text: str, limit: int) -> str:
    text = _clean(text)
    if len(text) <= limit:
        return text
    return _clean(text[:limit].rsplit(" ", 1)[0]) + "."


def _make_rewritten_problem(problem: str, insight: str, angle: str) -> str:
    base = _first_nonempty(problem, angle, insight, fallback="o problema real está sendo lido de forma frouxa")
    base = _replace_weak_patterns(base)
    if "problema" not in _normalize(base):
        base = f"O problema real é {base[0].lower() + base[1:]}" if len(base) > 1 else base
    return _truncate(base, 120)


def _make_rewritten_payoff(payoff: str, insight: str, problem: str) -> str:
    base = _first_nonempty(payoff, insight, problem, fallback="a decisão fica mais clara, mais concreta e mais útil")
    base = _replace_weak_patterns(base)
    normalized = _normalize(base)
    if all(token not in normalized for token in ("claro", "concret", "util", "criterio", "decis")):
        base = f"{base}. Isso deixa a leitura mais clara e mais útil na prática."
    return _truncate(base, 130)


def _make_rewritten_cta(cta: str) -> str:
    base = _replace_weak_patterns(cta)
    normalized = _normalize(base)
    blocked = ("comente aqui", "corre", "agora", "chama na dm", "clica no link")
    if not base or any(token in normalized for token in blocked):
        return "Salve para revisar antes da próxima decisão e envie para alguém que precisa disso com mais clareza."
    if "salve" not in normalized:
        return "Salve para revisar antes da próxima decisão e envie para alguém que precisa disso com mais clareza."
    return _truncate(base, 110)


def _make_headline(problem: str, payoff: str) -> str:
    problem = _clean(problem)
    payoff = _clean(payoff)
    headline = f"{problem.rstrip('.')}."
    if len(headline) < 28:
        headline = f"{problem.rstrip('.')} — e por isso o resultado continua frouxo."
    if len(headline) > 82:
        headline = _truncate(payoff or problem, 78)
    return _truncate(headline, 82)


def _make_hook(problem: str, insight: str) -> str:
    base = _first_nonempty(insight, problem, fallback="O problema raramente está onde parece.")
    base = _replace_weak_patterns(base)
    if len(base) < 48:
        base = f"O problema raramente está na falta de vontade. Quase sempre ele aparece quando a leitura do problema já começa frouxa. {base}"
    return _truncate(base, 150)


def _make_body(problem: str, insight: str, payoff: str) -> str:
    parts = [
        _make_rewritten_problem(problem, insight, ""),
        _replace_weak_patterns(insight),
        _make_rewritten_payoff(payoff, insight, problem),
    ]
    body = " ".join(part for part in parts if _clean(part))
    if len(body) < 120:
        body += " O ponto não é parecer profundo. O ponto é produzir leitura útil, critério melhor e ação mais limpa."
    return _truncate(body, 260)


def _support_points(problem: str, insight: str, payoff: str) -> list[str]:
    points = [
        _truncate(_make_rewritten_problem(problem, insight, ""), 72),
        _truncate(_replace_weak_patterns(insight) or "O custo real nasce antes da quebra visível.", 72),
        _truncate(_make_rewritten_payoff(payoff, insight, problem), 72),
    ]
    unique: list[str] = []
    for item in points:
        if item and item not in unique:
            unique.append(item)
    return unique[:3]


def _guardrails(text: str) -> dict[str, Any]:
    normalized = _normalize(text)
    flags: list[str] = []

    if any(token in normalized for token in ("acredite em voce", "coach", "sua melhor versao")):
        flags.append("coach_tone")
    if any(token in normalized for token in ("segredo", "viral", "imperdivel", "mude sua vida")):
        flags.append("cheap_copy")
    if any(token in normalized for token in ("energia do universo", "manifestar", "frequencia")):
        flags.append("cheap_self_help")
    if len(normalized) < 40:
        flags.append("abstract_or_thin")
    if normalized.count("muito") >= 2:
        flags.append("inflated_copy")

    return {
        "ok": not flags,
        "flags": flags,
        "blocked_cheap_coach": "coach_tone" in flags,
        "blocked_cheap_self_help": "cheap_self_help" in flags,
        "blocked_cheap_ai_copy": "cheap_copy" in flags,
        "blocked_abstract_void": "abstract_or_thin" in flags,
    }


def build_perceived_value_rewriter(raw_payload: dict[str, Any] | None) -> dict[str, Any]:
    raw_payload = _safe_dict(raw_payload)
    lexicon = get_brand_lexicon()

    raw_problem = _first_nonempty(raw_payload.get("problem"), raw_payload.get("angle"))
    raw_insight = _first_nonempty(raw_payload.get("insight"))
    raw_payoff = _first_nonempty(raw_payload.get("payoff"), raw_payload.get("body"))
    raw_cta = _first_nonempty(raw_payload.get("cta"), raw_payload.get("CTA"))

    rewritten_problem = _make_rewritten_problem(raw_problem, raw_insight, raw_payload.get("angle"))
    rewritten_payoff = _make_rewritten_payoff(raw_payoff, raw_insight, raw_problem)
    rewritten_cta = _make_rewritten_cta(raw_cta)

    authority_payload = {
        "headline": _make_headline(rewritten_problem, rewritten_payoff),
        "hook": _make_hook(rewritten_problem, raw_insight),
        "body": _make_body(rewritten_problem, raw_insight, rewritten_payoff),
        "cta": rewritten_cta,
        "support_points": _support_points(rewritten_problem, raw_insight, rewritten_payoff),
        "problem": rewritten_problem,
        "payoff": rewritten_payoff,
    }

    full_text = " ".join(
        [
            authority_payload["headline"],
            authority_payload["hook"],
            authority_payload["body"],
            authority_payload["cta"],
            " ".join(authority_payload["support_points"]),
        ]
    )

    alignment = scan_brand_alignment(full_text, lexicon)
    guardrails = _guardrails(full_text)

    authority_reason = (
        "rewrite focado em utilidade concreta, payoff claro, autoridade sóbria e redução de abstração"
    )
    if not guardrails["ok"]:
        authority_reason += "; guardrails detectaram sinais de commodity que precisam de revisão"

    rewritten_payload = {
        "problem": rewritten_problem,
        "payoff": rewritten_payoff,
        "cta": rewritten_cta,
        "headline": authority_payload["headline"],
        "hook": authority_payload["hook"],
        "body": authority_payload["body"],
        "support_points": authority_payload["support_points"],
    }

    changed_fields = []
    for key in ("problem", "payoff", "cta", "headline", "hook", "body"):
        before = raw_payload.get(key)
        after = rewritten_payload.get(key)
        if before != after:
            changed_fields.append(
                {
                    "field": key,
                    "before": before,
                    "after": after,
                }
            )

    return {
        "ok": True,
        "perceived_value_hypothesis": "utilidade concreta + payoff claro + CTA sóbria elevam valor percebido sem inflar promessa",
        "rewritten_problem": rewritten_problem,
        "rewritten_payoff": rewritten_payoff,
        "rewritten_cta": rewritten_cta,
        "authority_payload": authority_payload,
        "authority_reason": authority_reason,
        "anti_commodity_guardrails": guardrails,
        "brand_alignment": alignment,
        "pre_rewrite_state": "raw_payload",
        "post_rewrite_state": "rewritten_authority_payload",
        "rewritten_payload": rewritten_payload,
        "raw_payload_vs_rewritten_payload": {
            "changed_fields": changed_fields,
            "changed_fields_count": len(changed_fields),
        },
    }
