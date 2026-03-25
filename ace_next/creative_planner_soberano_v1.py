from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Any

from .brand_lexicon import get_brand_lexicon, scan_brand_alignment
from .distribution_timing_v1 import build_distribution_context_v1
from .editorial_critic_v1 import evaluate_editorial_critic
from .serial_continuity_engine_v1 import build_serial_continuity_engine_v1

VALID_FORMATS = {"image", "carousel", "story", "reel"}
WEAK_INPUTS = {"", "teste", "teste real", "oi", "hello", "123"}
PLANNER_VERSION = "editorial_soberano_v1"


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(char)
    )


def _normalize(value: str) -> str:
    return _strip_accents(_clean(value)).lower()


def _keywords(topic_seed: str) -> list[str]:
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", topic_seed.lower())
    stopwords = {
        "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos", "e", "em",
        "mais", "menos", "na", "nas", "no", "nos", "o", "os", "ou", "para", "por", "que",
        "se", "sem", "sobre", "um", "uma", "uns", "umas",
    }
    unique: list[str] = []
    for word in words:
        if len(word) < 3 or word in stopwords:
            continue
        if word not in unique:
            unique.append(word)
    return unique[:8]


def _detect_domain(topic_seed: str) -> str:
    text = _normalize(topic_seed)
    families = {
        "faith": ["fe", "deus", "oracao", "jesus", "proposito", "espiritual"],
        "emotion": ["ansiedade", "medo", "mente", "emocional", "angustia", "paz"],
        "discipline": ["disciplina", "foco", "clareza", "execucao", "consistencia", "direcao"],
        "prosperity": ["prosperidade", "dinheiro", "escassez", "riqueza", "financeiro"],
        "branding": ["marca", "conteudo", "instagram", "autoridade", "posicionamento"],
    }
    best = "discipline"
    best_hits = 0
    for family, anchors in families.items():
        hits = sum(1 for item in anchors if item in text)
        if hits > best_hits:
            best_hits = hits
            best = family
    return best


def _choose_format(domain: str, format_hint: str | None) -> str:
    hint = (format_hint or "").strip().lower()
    if hint in VALID_FORMATS:
        return hint
    if domain == "emotion":
        return "story"
    if domain in {"branding", "prosperity"}:
        return "carousel"
    return "image"


def _sequel_for_format(value: str) -> str:
    normalized = _normalize(value)
    if normalized in {"reel", "carousel"}:
        return "high"
    if normalized == "story":
        return "medium"
    return "medium"


def _compose_editorial_payload(topic_seed: str, domain: str) -> dict[str, Any]:
    keywords = _keywords(topic_seed)
    primary = keywords[0] if len(keywords) > 0 else "clareza"
    secondary = keywords[1] if len(keywords) > 1 else "disciplina"
    tertiary = keywords[2] if len(keywords) > 2 else "direção"

    if domain == "faith":
        return {
            "problem": f"muita gente deseja {primary}, mas tenta sustentar isso sem {secondary}",
            "insight": f"{primary.capitalize()} sem {secondary} vira emoção passageira; com estrutura, vira postura",
            "angle": f"{topic_seed} deve sair do discurso e entrar em prática sustentada",
            "hook_family": "misread_reality",
            "hook": f"Muita gente chama isso de falta de fé, mas o erro costuma ser outro: tentar sustentar {primary} sem {secondary}.",
            "headline": f"Sem {secondary}, até {primary} perde força no cotidiano.",
            "narrative_tension": "convicção sem estrutura perde tração no dia comum",
            "payoff": "convicção passa a organizar prática real",
            "cta": "Salve para reler quando a convicção precisar virar prática e envie para alguém que precisa alinhar fé com estrutura.",
            "body": f"O ponto não é sentir mais. O ponto é organizar melhor. Quando {primary} fica solta, ela depende do humor do dia. Quando {secondary} entra, a decisão ganha continuidade. E quando {tertiary} assume comando, a convicção deixa de ser discurso bonito e começa a virar rotina viva.",
            "support_points": [
                f"{primary.capitalize()} sem prática vira impulso.",
                f"{secondary.capitalize()} sustenta constância nos dias comuns.",
                f"{tertiary.capitalize()} protege a decisão quando a emoção oscila.",
            ],
        }
    if domain == "emotion":
        return {
            "problem": f"{primary} cresce quando a mente reage antes de ler a situação com {secondary}",
            "insight": "nem todo peso emocional é o centro da questão; muitas vezes a leitura ruim amplia tudo",
            "angle": f"{topic_seed} deve ser tratado com leitura, eixo e resposta, não com reação automática",
            "hook_family": "hidden_cost",
            "hook": f"Nem sempre o peso de {primary} é o problema principal. Muitas vezes o desgaste explode porque tudo está sendo lido sem {secondary}.",
            "headline": f"Sem {secondary}, {primary} ocupa o dia inteiro.",
            "narrative_tension": "reação automática transforma ruído em ameaça",
            "payoff": "clareza reduz desgaste e devolve domínio interno",
            "cta": "Salve para usar como lembrete de eixo e envie para quem precisa recuperar leitura antes da próxima reação.",
            "body": f"Sem {secondary}, qualquer ruído parece urgência. Quando {tertiary} entra, a mente volta a diferenciar pressão real de reação automática. O resultado não é perfeição instantânea. É menos desgaste, mais lucidez e resposta melhor.",
            "support_points": [
                f"{secondary.capitalize()} corta reação automática.",
                f"{tertiary.capitalize()} devolve leitura antes da resposta.",
                f"{primary.capitalize()} perde força quando o eixo volta ao lugar.",
            ],
        }
    if domain == "branding":
        return {
            "problem": f"{primary} sem identidade e sem {secondary} vira só mais uma peça no ruído",
            "insight": "marca forte não nasce de volume; nasce de recorte, hierarquia e utilidade real",
            "angle": f"{topic_seed} precisa sair da estética de produção e entrar em lógica de posicionamento",
            "hook_family": "identity_break",
            "hook": f"O problema raramente é falta de conteúdo. O problema é produzir {primary} sem {secondary}, sem recorte e sem uma leitura clara de {tertiary}.",
            "headline": f"Sem {secondary}, {primary} parece só mais do mesmo.",
            "narrative_tension": "volume sem identidade corrói autoridade",
            "payoff": "a mensagem ganha nitidez, valor percebido e presença editorial",
            "cta": "Salve como régua editorial e envie para quem precisa parar de produzir volume vazio.",
            "body": f"Marca não cresce com excesso de postagem. Cresce quando a mensagem tem eixo, quando a forma reforça a ideia e quando o público percebe valor rápido. É isso que separa presença editorial de feed commodity.",
            "support_points": [
                f"{secondary.capitalize()} separa posicionamento de volume vazio.",
                f"{tertiary.capitalize()} aumenta nitidez de mensagem e de público.",
                f"{primary.capitalize()} só ganha força quando carrega utilidade real.",
            ],
        }
    if domain == "prosperity":
        return {
            "problem": f"{primary} buscada com pressa e sem {secondary} vira expectativa, não construção",
            "insight": "resultado responde melhor a processo previsível do que a ansiedade por avanço",
            "angle": f"{topic_seed} só ganha consistência quando a base é estruturada",
            "hook_family": "discipline_reframe",
            "hook": f"O travamento quase nunca nasce da falta de vontade. Na maioria das vezes ele nasce de buscar {primary} sem construir {secondary}.",
            "headline": f"Sem {secondary}, {primary} vira só expectativa.",
            "narrative_tension": "pressa sem base corrói consistência",
            "payoff": "o tema sai do abstrato e entra na execução concreta",
            "cta": "Salve isso como régua de execução e compartilhe com quem precisa trocar pressa por construção.",
            "body": f"Resultado não respeita ansiedade. Respeita base. Quando {secondary} sustenta o processo e {tertiary} organiza prioridade, o tema deixa de soar abstrato e começa a responder à execução real.",
            "support_points": [
                f"{secondary.capitalize()} reduz desperdício de energia.",
                f"{tertiary.capitalize()} protege foco contra distração.",
                f"{primary.capitalize()} fica concreto quando a base é previsível.",
            ],
        }
    return {
        "problem": f"{primary} sem {secondary} perde forma antes de virar resultado",
        "insight": "ideia boa sozinha não sustenta mudança; ela precisa de estrutura, repetição e leitura",
        "angle": f"{topic_seed} melhora quando sai da frase bonita e entra em critério",
        "hook_family": "discipline_reframe",
        "hook": f"O problema raramente é falta de esforço. Quase sempre é tentar sustentar {primary} sem {secondary}, como se intenção sozinha bastasse.",
        "headline": f"Sem {secondary}, {primary} perde força antes de virar resultado.",
        "narrative_tension": "boa intenção sem eixo se dispersa no ruído",
        "payoff": "execução ganha forma e direção",
        "cta": "Salve para revisar antes da próxima decisão e envie para alguém que precisa de mais critério e menos ruído.",
        "body": f"Ideia boa sozinha não sustenta mudança. Ela precisa de {secondary} para ganhar forma e de {tertiary} para não se perder no meio do caminho. Quando isso acontece, o tema deixa de soar abstrato e começa a servir para decisão real.",
        "support_points": [
            f"{primary.capitalize()} sem base vira intenção solta.",
            f"{secondary.capitalize()} sustenta execução quando o entusiasmo cai.",
            f"{tertiary.capitalize()} organiza prioridade e protege consistência.",
        ],
    }


def _llm_planner_enabled() -> bool:
    return str(os.environ.get("ACE_USE_LLM_PLANNER", "0")).strip().lower() in {"1", "true", "yes", "on"}


def _extract_json_block(raw_text: str) -> str | None:
    if not raw_text:
        return None
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return raw_text[start:end + 1]


def _safe_parse_json(raw_text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(raw_text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _normalize_support_points(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    cleaned: list[str] = []
    for item in value:
        text = _clean(str(item))
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned[:5]


def _build_deterministic_payload(topic_seed: str, domain: str, format_hint: str | None) -> dict[str, Any]:
    payload = dict(_compose_editorial_payload(topic_seed, domain))
    payload["format_recommendation"] = _choose_format(domain, format_hint)
    payload["sequel_potential"] = _sequel_for_format(payload["format_recommendation"])
    return payload


def _build_llm_prompt(
    *,
    topic_seed: str,
    domain: str,
    format_hint: str | None,
    signal_context: dict[str, Any],
    brand_context: dict[str, Any],
) -> str:
    preferred_format = _choose_format(domain, format_hint)
    series_name = _clean(str(brand_context.get("series_name") or "Liberta a Verdade"))

    return f"""
Você é o planner editorial soberano do ACE Ω.
Sua tarefa é gerar um plano editorial premium em JSON puro.

Regras absolutas:
- sem markdown
- sem comentários
- sem texto fora do JSON
- linguagem premium
- anti-coach genérico
- anti-clichê
- anti-commodity
- anti-frase vazia
- proibido usar expressões como "ninguém te conta", "segredo", "acredite em você", "sua vida vai mudar"
- clareza, tensão, valor percebido e naturalidade
- o texto deve soar humano, firme e inteligente
- suporte em português do Brasil

Contexto:
- topic_seed: {topic_seed}
- domain: {domain}
- preferred_format: {preferred_format}
- series_name: {series_name}
- signal_context: {json.dumps(signal_context, ensure_ascii=False)}
- brand_context: {json.dumps(brand_context, ensure_ascii=False)}

Retorne JSON com ESTES campos:
{{
  "problem": "string",
  "insight": "string",
  "angle": "string",
  "hook_family": "string",
  "hook": "string",
  "headline": "string",
  "narrative_tension": "string",
  "payoff": "string",
  "cta": "string",
  "body": "string",
  "support_points": ["string", "string", "string"],
  "format_recommendation": "image|carousel|story|reel",
  "sequel_potential": "low|medium|high"
}}
""".strip()


def _validate_llm_payload(
    payload: dict[str, Any],
    *,
    domain: str,
    format_hint: str | None,
) -> dict[str, Any] | None:
    required_string_fields = [
        "problem",
        "insight",
        "angle",
        "hook_family",
        "hook",
        "headline",
        "narrative_tension",
        "payoff",
        "cta",
        "body",
    ]

    normalized: dict[str, Any] = {}
    for field in required_string_fields:
        value = payload.get(field)
        if not isinstance(value, str):
            return None
        cleaned = _clean(value)
        if not cleaned:
            return None
        normalized[field] = cleaned

    support_points = _normalize_support_points(payload.get("support_points"))
    if len(support_points) < 2:
        return None
    normalized["support_points"] = support_points

    format_recommendation = _normalize(str(payload.get("format_recommendation") or ""))
    if format_recommendation not in VALID_FORMATS:
        format_recommendation = _choose_format(domain, format_hint)
    normalized["format_recommendation"] = format_recommendation

    sequel_potential = _normalize(str(payload.get("sequel_potential") or ""))
    if sequel_potential not in {"low", "medium", "high"}:
        sequel_potential = _sequel_for_format(format_recommendation)
    normalized["sequel_potential"] = sequel_potential

    return normalized


def _looks_generic(payload: dict[str, Any], lexicon: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(payload.get("headline") or ""),
            str(payload.get("hook") or ""),
            str(payload.get("body") or ""),
            str(payload.get("cta") or ""),
            " ".join(payload.get("support_points") or []),
        ]
    )
    normalized = _normalize(text)

    banned_fragments = {
        "ninguem te conta",
        "segredo",
        "acredite em voce",
        "sua vida vai mudar",
        "descubra o segredo",
        "mude sua vida",
    }

    if any(fragment in normalized for fragment in banned_fragments):
        return True

    for pattern in lexicon.get("disallowed_patterns") or []:
        if _normalize(str(pattern)) and _normalize(str(pattern)) in normalized:
            return True

    if len(_clean(str(payload.get("headline") or ""))) < 14:
        return True
    if len(_clean(str(payload.get("hook") or ""))) < 24:
        return True
    if len(_clean(str(payload.get("body") or ""))) < 80:
        return True
    if len(payload.get("support_points") or []) < 2:
        return True

    return False


def _llm_payload(
    *,
    topic_seed: str,
    domain: str,
    format_hint: str | None,
    signal_context: dict[str, Any],
    brand_context: dict[str, Any],
    lexicon: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any], str]:
    if not _llm_planner_enabled():
        return (
            None,
            {
                "attempted": False,
                "provider": None,
                "ok": False,
                "reason": "llm_planner_disabled",
            },
            "deterministic",
        )

    try:
        from .llm_orchestrator import generate_text, llm_orchestrator_status
    except Exception as exc:
        return (
            None,
            {
                "attempted": False,
                "provider": None,
                "ok": False,
                "reason": f"orchestrator_unavailable:{type(exc).__name__}",
            },
            "llm_fallback_to_deterministic",
        )

    try:
        _ = llm_orchestrator_status()
    except Exception:
        pass

    prompt = _build_llm_prompt(
        topic_seed=topic_seed,
        domain=domain,
        format_hint=format_hint,
        signal_context=signal_context,
        brand_context=brand_context,
    )

    result = generate_text("planner", prompt)
    provider = result.get("provider")

    llm_status = {
        "attempted": True,
        "provider": provider,
        "ok": False,
        "reason": None,
    }

    if not result.get("ok"):
        llm_status["reason"] = str(result.get("reason") or "llm_generation_failed")
        return None, llm_status, "llm_fallback_to_deterministic"

    raw_output = str(result.get("result") or "")
    json_block = _extract_json_block(raw_output)
    if not json_block:
        llm_status["reason"] = "json_block_not_found"
        return None, llm_status, "llm_fallback_to_deterministic"

    parsed = _safe_parse_json(json_block)
    if not parsed:
        llm_status["reason"] = "json_parse_failed"
        return None, llm_status, "llm_fallback_to_deterministic"

    validated = _validate_llm_payload(
        parsed,
        domain=domain,
        format_hint=format_hint,
    )
    if not validated:
        llm_status["reason"] = "invalid_json_contract"
        return None, llm_status, "llm_fallback_to_deterministic"

    if _looks_generic(validated, lexicon):
        llm_status["reason"] = "generic_or_commodity_llm_output"
        return None, llm_status, "llm_fallback_to_deterministic"

    llm_status["ok"] = True
    llm_status["reason"] = None
    return validated, llm_status, "llm_assisted"


def _collect_memory_context(signal_context: dict[str, Any], brand_context: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for source in [brand_context, signal_context]:
        for key in [
            "ace_content_history",
            "ace_candidate_posts",
            "recent_posts",
            "recent_content",
            "episodic_performance_memory",
            "experiment_registry",
            "performance_context",
        ]:
            if key in source and source.get(key) is not None:
                merged[key] = source.get(key)
    return merged


def _perceived_value_hypothesis(payload: dict[str, Any], domain: str) -> str:
    if domain == "branding":
        return "clareza de recorte + utilidade rápida + identidade forte aumentam salvamento e autoridade percebida"
    if domain == "emotion":
        return "tensão real + clareza prática + densidade baixa aumentam leitura completa e compartilhamento íntimo"
    if domain == "prosperity":
        return "processo concreto + payoff aplicável aumentam save rate e comentário de reconhecimento"
    return "fricção real + payoff concreto + CTA sóbria aumentam valor percebido sem cheirar a commodity"


def _fallback_flags(planner_generation_mode: str, llm_status: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    if planner_generation_mode == "deterministic":
        flags.append("deterministic_path")
    if planner_generation_mode == "llm_fallback_to_deterministic":
        flags.append("llm_fallback_to_deterministic")
    if llm_status.get("reason"):
        flags.append(str(llm_status.get("reason")))
    return flags


def _official_path_quality_state(critic: dict[str, Any]) -> str:
    caption_gate = critic.get("caption_gate") or {}
    if critic.get("approved") and caption_gate.get("approved"):
        return "approved"
    if critic.get("failed_floors"):
        return "needs_rewrite"
    return "conservative_fallback"


def _finalize_plan(
    *,
    topic_seed: str,
    domain: str,
    payload: dict[str, Any],
    lexicon: dict[str, Any],
    brand_context: dict[str, Any],
    signal_context: dict[str, Any],
    planner_generation_mode: str,
    llm_status: dict[str, Any],
) -> dict[str, Any]:
    body = payload["body"]
    support_points = list(payload["support_points"])
    full_text = " ".join([payload["headline"], payload["hook"], body, payload["cta"], *support_points])

    alignment = scan_brand_alignment(full_text, lexicon)
    critic = evaluate_editorial_critic(payload, lexicon)
    caption_gate = critic.get("caption_gate") or {}

    memory_context = _collect_memory_context(signal_context, brand_context)
    serial_continuity = build_serial_continuity_engine_v1(
        topic_seed=topic_seed,
        hook=payload["hook"],
        angle=payload["angle"],
        sequel_potential=payload["sequel_potential"],
        memory_context=memory_context,
        series_name=brand_context.get("series_name"),
    )
    distribution_context = build_distribution_context_v1(
        format_recommendation=payload["format_recommendation"],
        serial_continuity=serial_continuity,
        performance_context=memory_context.get("performance_context"),
        signal_context=signal_context,
    )

    series_name = serial_continuity.get("series_name") or brand_context.get("series_name") or lexicon["brand_name"]
    deterministic_path = planner_generation_mode != "llm_assisted"
    fallback_flags = _fallback_flags(planner_generation_mode, llm_status)
    official_path_quality_state = _official_path_quality_state(critic)

    notes = [
        "planner_selected=creative_planner_soberano_v1",
        f"planner_generation_mode={planner_generation_mode}",
        f"editorial_critic_approved={critic.get('approved')}",
        f"caption_gate_approved={caption_gate.get('approved')}",
        f"serial_candidate={serial_continuity.get('sequel_candidate')}",
        f"distribution_source_mode={distribution_context.get('source_mode')}",
    ]
    if llm_status.get("provider"):
        notes.append(f"llm_provider={llm_status.get('provider')}")
    if llm_status.get("reason"):
        notes.append(f"llm_reason={llm_status.get('reason')}")

    return {
        "ok": True,
        "topic_seed": topic_seed,
        "problem": payload["problem"],
        "insight": payload["insight"],
        "angle": payload["angle"],
        "hook_family": payload["hook_family"],
        "hook": payload["hook"],
        "headline": payload["headline"],
        "body": body,
        "support_points": support_points,
        "narrative_tension": payload["narrative_tension"],
        "payoff": payload["payoff"],
        "cta": payload["cta"],
        "format_recommendation": payload["format_recommendation"],
        "strategic_target_format": payload["format_recommendation"],
        "sequel_potential": payload["sequel_potential"],
        "series_name": series_name,
        "continuation_candidate": bool(serial_continuity.get("sequel_candidate")),
        "brand_lexicon_hits": alignment["semantic_anchors"] + alignment["approved_language_patterns"][:2],
        "brand_fit_signals": alignment["semantic_anchors"] + alignment["approved_language_patterns"][:2],
        "anti_generic_risk": "high" if "anti_genericity" in (critic.get("failed_floors") or []) else "low",
        "perceived_value_hypothesis": _perceived_value_hypothesis(payload, domain),
        "timing_hypothesis": distribution_context.get("timing_hypothesis"),
        "planner_version": PLANNER_VERSION,
        "planner_mode": planner_generation_mode,
        "deterministic": deterministic_path,
        "deterministic_path": deterministic_path,
        "serial_continuity": serial_continuity,
        "distribution_context": distribution_context,
        "critic": critic,
        "editorial_critic": critic,
        "caption_gate": caption_gate,
        "planner_selected": "creative_planner_soberano_v1",
        "llm_status": llm_status,
        "fallback_flags": fallback_flags,
        "official_path_quality_state": official_path_quality_state,
        "notes": notes,
    }


def build_creative_plan_soberano_v1(
    topic_seed: str,
    signal_context: dict | None = None,
    brand_context: dict | None = None,
    format_hint: str | None = None,
) -> dict[str, Any]:
    signal_context = dict(signal_context or {})
    brand_context = dict(brand_context or {})
    lexicon = get_brand_lexicon()

    topic_seed = _clean(topic_seed or "clareza, disciplina e direção")
    if _normalize(topic_seed) in WEAK_INPUTS:
        topic_seed = "clareza, disciplina e direção"

    domain = _detect_domain(topic_seed)
    deterministic_payload = _build_deterministic_payload(topic_seed, domain, format_hint)

    llm_payload, llm_status, planner_generation_mode = _llm_payload(
        topic_seed=topic_seed,
        domain=domain,
        format_hint=format_hint,
        signal_context=signal_context,
        brand_context=brand_context,
        lexicon=lexicon,
    )

    if llm_payload is not None:
        payload = llm_payload
    else:
        payload = deterministic_payload
        if planner_generation_mode not in {"deterministic", "llm_fallback_to_deterministic"}:
            planner_generation_mode = "deterministic"

    return _finalize_plan(
        topic_seed=topic_seed,
        domain=domain,
        payload=payload,
        lexicon=lexicon,
        brand_context=brand_context,
        signal_context=signal_context,
        planner_generation_mode=planner_generation_mode,
        llm_status=llm_status,
    )


def planner_soberano_examples() -> dict[str, Any]:
    approved = build_creative_plan_soberano_v1("clareza, disciplina e direção")
    rejected_like = {
        "topic_seed": "mudança de vida",
        "problem": "vida travada",
        "insight": "acredite em você",
        "angle": "motivação",
        "hook_family": "coach_generic",
        "hook": "Descubra o segredo que ninguém te conta",
        "headline": "Acredite em você e tudo vai mudar",
        "narrative_tension": "vaga",
        "payoff": "sua vida vai melhorar",
        "cta": "Comente aqui",
        "format_recommendation": "image",
        "sequel_potential": "low",
        "critic": evaluate_editorial_critic(
            {
                "headline": "Acredite em você e tudo vai mudar",
                "hook": "Descubra o segredo que ninguém te conta",
                "body": "Sua vida pode mudar agora.",
                "cta": "Comente aqui",
                "payoff": "",
                "narrative_tension": "",
            }
        ),
    }
    return {
        "ok": True,
        "approved_example": approved,
        "rejected_example": rejected_like,
    }
