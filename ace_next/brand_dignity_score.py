from __future__ import annotations

from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _normalize_format(value: Any) -> str:
    normalized = _clean_text(value).lower()
    if normalized in {"story", "stories"}:
        return "story"
    if normalized in {"carousel", "image"}:
        return normalized
    return "image"


def _text_signal(value: str) -> bool:
    text = _clean_text(value).lower()
    banned = {
        "ninguém te conta",
        "ninguem te conta",
        "segredo",
        "mude sua vida",
        "sua vida vai mudar",
        "acredite em você",
        "acredite em voce",
        "isso muda tudo",
    }
    return any(item in text for item in banned)


def _cta_signal(value: str) -> bool:
    text = _clean_text(value).lower()
    cheap = {
        "comente aqui",
        "corre",
        "chama na dm",
        "clica no link agora",
        "não perde",
        "nao perde",
        "compra agora",
    }
    return any(item in text for item in cheap)


def _headline_signal(value: str) -> bool:
    text = _clean_text(value).lower()
    generic = {
        "descubra",
        "segredo",
        "ninguém te conta",
        "ninguem te conta",
        "isso muda tudo",
        "você precisa",
        "voce precisa",
    }
    return any(item in text for item in generic)


def _classify(final_score: float, failed_floors: list[str], generic_phrase: bool, cheap_cta: bool) -> str:
    if len(failed_floors) >= 3 or (generic_phrase and cheap_cta):
        return "brand_indignity"
    if final_score < 7.6:
        return "commodity_risk"
    if final_score < 8.1:
        return "borderline"
    if final_score < 8.7:
        return "acceptable"
    return "premium"


def evaluate_brand_dignity_score(
    *,
    creative_plan: dict | None = None,
    visual_qa: dict | None = None,
    hierarchy_gate: dict | None = None,
    template_meta: dict | None = None,
) -> dict:
    creative_plan = _safe_dict(creative_plan)
    visual_qa = _safe_dict(visual_qa)
    hierarchy_gate = _safe_dict(hierarchy_gate)
    template_meta = _safe_dict(template_meta)

    strategic_format = _normalize_format(
        creative_plan.get("strategic_target_format")
        or creative_plan.get("publish_format_now")
        or creative_plan.get("format_recommendation")
    )

    headline = _clean_text(creative_plan.get("headline"))
    hook = _clean_text(creative_plan.get("hook"))
    body = _clean_text(creative_plan.get("body"))
    cta = _clean_text(creative_plan.get("cta"))

    support_points = creative_plan.get("support_points")
    if not isinstance(support_points, list):
        support_points = []
    support_points = [_clean_text(x) for x in support_points if _clean_text(x)]

    compaction_report = _safe_dict(creative_plan.get("compaction_report"))
    hidden_overflow_count = int(compaction_report.get("hidden_overflow_count") or 0)

    visual_score_seen = _safe_float(visual_qa.get("final_score"))
    if visual_score_seen is not None and visual_score_seen > 10:
        visual_score_seen = round(visual_score_seen / 10.0, 2)

    hierarchy_score_seen = _safe_float(hierarchy_gate.get("final_score"))
    if hierarchy_score_seen is not None and hierarchy_score_seen > 10:
        hierarchy_score_seen = round(hierarchy_score_seen / 10.0, 2)

    template_id = _clean_text(template_meta.get("template_id"))
    premium_template_used = bool(template_meta.get("premium_tier")) or template_id.endswith("_v1")

    generic_phrase_detected = _headline_signal(headline) or _text_signal(" ".join([headline, hook, body]))
    cheap_cta_detected = _cta_signal(cta)

    support_limit = 1 if strategic_format == "story" else 2
    cta_limit = 42 if strategic_format == "story" else 48
    body_limit = 120 if strategic_format == "story" else 210

    brand_fit = 8.5 if premium_template_used else 7.4
    anti_commodity = 8.4 if not generic_phrase_detected else 6.5
    premium_feel = 8.3 if premium_template_used else 7.2
    clarity = 8.4 if len(headline) <= 92 and len(cta) <= cta_limit and len(body) <= body_limit else 7.1
    visual_dignity = hierarchy_score_seen or visual_score_seen or 7.1
    naturality = 8.3 if not generic_phrase_detected and not cheap_cta_detected else 6.8

    if len(support_points) > support_limit:
        premium_feel -= 0.8
        clarity -= 0.4
    if cheap_cta_detected:
        premium_feel -= 0.8
        anti_commodity -= 0.6
        naturality -= 0.5
    if generic_phrase_detected:
        brand_fit -= 0.6
        anti_commodity -= 1.0
        naturality -= 0.7
    if len(cta) > cta_limit:
        clarity -= 0.8
        premium_feel -= 0.5
    if len(hook) > 120:
        anti_commodity -= 0.3
        premium_feel -= 0.4
    if hidden_overflow_count > 0 and len(support_points) <= support_limit:
        clarity += 0.2

    breakdown = {
        "brand_fit": round(max(0.0, min(10.0, brand_fit)), 2),
        "anti_commodity": round(max(0.0, min(10.0, anti_commodity)), 2),
        "premium_feel": round(max(0.0, min(10.0, premium_feel)), 2),
        "clarity": round(max(0.0, min(10.0, clarity)), 2),
        "visual_dignity": round(max(0.0, min(10.0, visual_dignity)), 2),
        "naturality": round(max(0.0, min(10.0, naturality)), 2),
    }

    floors = {
        "brand_fit": 8.3,
        "anti_commodity": 8.0,
        "premium_feel": 7.8,
        "clarity": 7.8,
        "visual_dignity": 7.8,
        "naturality": 7.8,
    }

    failed_floors = [key for key, minimum in floors.items() if breakdown[key] < minimum]

    reasons: list[str] = []
    recommendations: list[str] = []

    if generic_phrase_detected:
        reasons.append("headline ou texto com traço commodity")
        recommendations.append("remover frase genérica e elevar o ângulo")
    if cheap_cta_detected:
        reasons.append("CTA vulgar ou pedinte")
        recommendations.append("substituir CTA por orientação mais sóbria")
    if len(support_points) > support_limit:
        reasons.append("support points em excesso")
        recommendations.append("reduzir support points visíveis")
    if len(cta) > cta_limit:
        reasons.append("CTA longa demais para o formato")
        recommendations.append("encurtar CTA")
    if not premium_template_used:
        reasons.append("template premium não detectado")
        recommendations.append("usar template premium explícito")
    if hierarchy_score_seen is not None and hierarchy_score_seen < 7.8:
        reasons.append("hierarquia visual ainda fraca")
        recommendations.append("reforçar hierarchy gate antes de aprovar")

    final_score = round(sum(breakdown.values()) / len(breakdown), 2)
    classification = _classify(final_score, failed_floors, generic_phrase_detected, cheap_cta_detected)
    approved = classification in {"premium", "acceptable"} and not failed_floors

    signals = {
        "headline_chars": len(headline),
        "hook_chars": len(hook),
        "body_chars": len(body),
        "cta_chars": len(cta),
        "support_points_count": len(support_points),
        "premium_template_used": premium_template_used,
        "generic_phrase_detected": generic_phrase_detected,
        "cheap_cta_detected": cheap_cta_detected,
        "visual_score_seen": visual_score_seen,
        "hierarchy_score_seen": hierarchy_score_seen,
        "hidden_overflow_count": hidden_overflow_count,
        "format": strategic_format,
    }

    if not reasons:
        reasons.append("peça mantém dignidade visual/editorial aceitável")

    return {
        "ok": True,
        "approved": approved,
        "final_score": final_score,
        "classification": classification,
        "breakdown": breakdown,
        "failed_floors": failed_floors,
        "reasons": reasons,
        "recommendations": recommendations,
        "signals": signals,
    }


def brand_dignity_score_examples() -> dict:
    premium = evaluate_brand_dignity_score(
        creative_plan={
            "headline": "Sem disciplina, clareza perde força antes de virar resultado.",
            "hook": "O problema raramente é falta de esforço.",
            "body": "Estrutura transforma intenção em direção real.",
            "cta": "Salve para revisar antes da próxima decisão.",
            "support_points": ["Clareza sem base vira intenção solta.", "Disciplina protege consistência."],
            "format_recommendation": "image",
            "compaction_report": {"hidden_overflow_count": 1},
        },
        visual_qa={"final_score": 84},
        hierarchy_gate={"final_score": 82},
        template_meta={"premium_tier": "premium_core", "template_id": "hero_card_v1"},
    )
    borderline = evaluate_brand_dignity_score(
        creative_plan={
            "headline": "Você precisa ver isso agora.",
            "cta": "Salve se fez sentido.",
            "support_points": ["Mais foco.", "Mais resultado.", "Mais disciplina."],
            "format_recommendation": "image",
        },
        visual_qa={"final_score": 79},
        hierarchy_gate={"final_score": 77},
        template_meta={"premium_tier": "premium_core", "template_id": "hero_card_v1"},
    )
    commodity = evaluate_brand_dignity_score(
        creative_plan={
            "headline": "Descubra o segredo que ninguém te conta.",
            "hook": "Isso muda tudo agora.",
            "body": "Sua vida vai mudar agora.",
            "cta": "Comente aqui agora.",
            "support_points": ["Mais foco.", "Mais energia.", "Mais resultado.", "Mais motivação."],
            "format_recommendation": "image",
        },
        visual_qa={"final_score": 72},
        hierarchy_gate={"final_score": 70},
        template_meta={},
    )
    return {
        "ok": True,
        "premium_example": premium,
        "borderline_example": borderline,
        "commodity_risk_example": commodity,
    }
