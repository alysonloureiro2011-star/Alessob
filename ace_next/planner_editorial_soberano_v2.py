from __future__ import annotations

import re
import unicodedata
from typing import Any

from .brand_lexicon import get_brand_lexicon, scan_brand_alignment
from .distribution_seriality_pack import build_distribution_seriality_pack
from .editorial_examples import examples_context
from .serial_continuity_engine_v1 import build_serial_continuity_engine_v1

PLANNER_VERSION = "editorial_soberano_v2"
VALID_FORMATS = {"image", "carousel", "story", "reel"}
WEAK_INPUTS = {"", "teste", "teste real", "oi", "hello", "123"}


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize(value: Any) -> str:
    raw = _clean(value).lower()
    return "".join(
        char for char in unicodedata.normalize("NFKD", raw)
        if not unicodedata.combining(char)
    )


def _keywords(topic_seed: str) -> list[str]:
    stopwords = {
        "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos", "e", "em",
        "mais", "menos", "na", "nas", "no", "nos", "o", "os", "ou", "para", "por", "que",
        "se", "sem", "sobre", "um", "uma", "uns", "umas",
    }
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", topic_seed.lower())
    unique: list[str] = []
    for word in words:
        if len(word) < 3 or word in stopwords:
            continue
        if word not in unique:
            unique.append(word)
    return unique[:8]


def _domain(topic_seed: str) -> str:
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


def _format_recommendation(domain: str, format_hint: str | None) -> str:
    hint = _normalize(format_hint or "")
    if hint in VALID_FORMATS:
        return hint
    if domain == "branding":
        return "carousel"
    if domain == "emotion":
        return "story"
    if domain == "prosperity":
        return "carousel"
    return "image"


def _sequel_potential(format_recommendation: str) -> str:
    if format_recommendation in {"carousel", "reel"}:
        return "high"
    if format_recommendation == "story":
        return "medium"
    return "medium"


def _perceived_value_hypothesis(domain: str) -> str:
    if domain == "branding":
        return "clareza de recorte + utilidade rápida + identidade forte aumentam salvamento e autoridade percebida"
    if domain == "emotion":
        return "tensão real + clareza prática + carga baixa aumentam leitura completa e compartilhamento íntimo"
    if domain == "prosperity":
        return "processo concreto + payoff aplicável aumentam save rate e comentário de reconhecimento"
    if domain == "faith":
        return "convicção concreta + estrutura prática aumentam salvamento e memorização"
    return "fricção real + payoff concreto + CTA sóbria aumentam valor percebido sem cheiro de commodity"


def _deterministic_editorial_payload(topic_seed: str, domain: str, format_hint: str | None) -> dict[str, Any]:
    keywords = _keywords(topic_seed)
    primary = keywords[0] if len(keywords) > 0 else "clareza"
    secondary = keywords[1] if len(keywords) > 1 else "disciplina"
    tertiary = keywords[2] if len(keywords) > 2 else "direção"
    format_recommendation = _format_recommendation(domain, format_hint)

    common = {
        "topic_seed": topic_seed,
        "format_recommendation": format_recommendation,
        "sequel_potential": _sequel_potential(format_recommendation),
    }

    if domain == "branding":
        return {
            **common,
            "problem": f"{primary} sem identidade e sem {secondary} vira só mais uma peça no ruído.",
            "insight": "marca forte não nasce de volume; nasce de recorte, hierarquia e utilidade real.",
            "angle": f"{topic_seed} precisa sair da estética de produção e entrar em lógica de posicionamento.",
            "hook_family": "identity_break",
            "hook": f"O problema raramente é falta de conteúdo. O problema é produzir {primary} sem {secondary}, sem recorte e sem hierarquia de mensagem.",
            "headline": f"Sem {secondary}, {primary} parece só mais do mesmo.",
            "body": f"Marca não cresce com excesso de postagem. Cresce quando a mensagem tem eixo, quando a forma reforça a ideia e quando o público percebe valor rápido. É isso que separa presença editorial de feed commodity.",
            "support_points": [
                f"{secondary.capitalize()} separa posicionamento de volume vazio.",
                f"{tertiary.capitalize()} aumenta nitidez de mensagem e de público.",
                f"{primary.capitalize()} só ganha força quando carrega utilidade real.",
            ],
            "narrative_tension": "volume sem identidade corrói autoridade.",
            "payoff": "a mensagem ganha nitidez, valor percebido e presença editorial.",
            "cta": "Salve como régua editorial e envie para quem precisa parar de produzir volume vazio.",
        }
    if domain == "emotion":
        return {
            **common,
            "problem": f"{primary} cresce quando a mente reage antes de ler a situação com {secondary}.",
            "insight": "nem todo peso emocional é o centro da questão; muitas vezes a leitura ruim amplia tudo.",
            "angle": f"{topic_seed} deve ser tratado com leitura, eixo e resposta, não com reação automática.",
            "hook_family": "hidden_cost",
            "hook": f"Nem sempre o peso de {primary} é o problema principal. Muitas vezes o desgaste explode porque tudo está sendo lido sem {secondary}.",
            "headline": f"Sem {secondary}, {primary} ocupa o dia inteiro.",
            "body": f"Sem {secondary}, qualquer ruído parece urgência. Quando {tertiary} entra, a mente volta a diferenciar pressão real de reação automática. O resultado não é perfeição instantânea. É menos desgaste, mais lucidez e resposta melhor.",
            "support_points": [
                f"{secondary.capitalize()} corta reação automática.",
                f"{tertiary.capitalize()} devolve leitura antes da resposta.",
                f"{primary.capitalize()} perde força quando o eixo volta ao lugar.",
            ],
            "narrative_tension": "reação automática transforma ruído em ameaça.",
            "payoff": "clareza reduz desgaste e devolve domínio interno.",
            "cta": "Salve para usar como lembrete de eixo e envie para quem precisa recuperar leitura antes da próxima reação.",
        }
    if domain == "prosperity":
        return {
            **common,
            "problem": f"{primary} buscada com pressa e sem {secondary} vira expectativa, não construção.",
            "insight": "resultado responde melhor a processo previsível do que a ansiedade por avanço.",
            "angle": f"{topic_seed} só ganha consistência quando a base é estruturada.",
            "hook_family": "discipline_reframe",
            "hook": f"O travamento quase nunca nasce da falta de vontade. Na maioria das vezes ele nasce de buscar {primary} sem construir {secondary}.",
            "headline": f"Sem {secondary}, {primary} vira só expectativa.",
            "body": f"Resultado não respeita ansiedade. Respeita base. Quando {secondary} sustenta o processo e {tertiary} organiza prioridade, o tema deixa de soar abstrato e começa a responder à execução real.",
            "support_points": [
                f"{secondary.capitalize()} reduz desperdício de energia.",
                f"{tertiary.capitalize()} protege foco contra distração.",
                f"{primary.capitalize()} fica concreto quando a base é previsível.",
            ],
            "narrative_tension": "pressa sem base corrói consistência.",
            "payoff": "o tema sai do abstrato e entra na execução concreta.",
            "cta": "Salve isso como régua de execução e compartilhe com quem precisa trocar pressa por construção.",
        }
    if domain == "faith":
        return {
            **common,
            "problem": f"muita gente deseja {primary}, mas tenta sustentar isso sem {secondary}.",
            "insight": f"{primary.capitalize()} sem {secondary} vira emoção passageira; com estrutura, vira postura.",
            "angle": f"{topic_seed} deve sair do discurso e entrar em prática sustentada.",
            "hook_family": "misread_reality",
            "hook": f"Muita gente chama isso de falta de fé, mas o erro costuma ser outro: tentar sustentar {primary} sem {secondary}.",
            "headline": f"Sem {secondary}, até {primary} perde força no cotidiano.",
            "body": f"O ponto não é sentir mais. O ponto é organizar melhor. Quando {primary} fica solta, ela depende do humor do dia. Quando {secondary} entra, a decisão ganha continuidade. E quando {tertiary} assume comando, a convicção deixa de ser discurso bonito e começa a virar rotina viva.",
            "support_points": [
                f"{primary.capitalize()} sem prática vira impulso.",
                f"{secondary.capitalize()} sustenta constância nos dias comuns.",
                f"{tertiary.capitalize()} protege a decisão quando a emoção oscila.",
            ],
            "narrative_tension": "convicção sem estrutura perde tração no dia comum.",
            "payoff": "convicção passa a organizar prática real.",
            "cta": "Salve para reler quando a convicção precisar virar prática e envie para alguém que precisa alinhar fé com estrutura.",
        }
    return {
        **common,
        "problem": f"{primary} sem {secondary} perde forma antes de virar resultado.",
        "insight": "ideia boa sozinha não sustenta mudança; ela precisa de estrutura, repetição e leitura.",
        "angle": f"{topic_seed} melhora quando sai da frase bonita e entra em critério.",
        "hook_family": "discipline_reframe",
        "hook": f"O problema raramente é falta de esforço. Quase sempre é tentar sustentar {primary} sem {secondary}, como se intenção sozinha bastasse.",
        "headline": f"Sem {secondary}, {primary} perde força antes de virar resultado.",
        "body": f"Ideia boa sozinha não sustenta mudança. Ela precisa de {secondary} para ganhar forma e de {tertiary} para não se perder no meio do caminho. Quando isso acontece, o tema deixa de soar abstrato e começa a servir para decisão real.",
        "support_points": [
            f"{primary.capitalize()} sem base vira intenção solta.",
            f"{secondary.capitalize()} sustenta execução quando o entusiasmo cai.",
            f"{tertiary.capitalize()} organiza prioridade e protege consistência.",
        ],
        "narrative_tension": "boa intenção sem eixo se dispersa no ruído.",
        "payoff": "execução ganha forma e direção.",
        "cta": "Salve para revisar antes da próxima decisão e envie para alguém que precisa de mais critério e menos ruído.",
    }


def _anti_commodity_flags(topic_seed: str, payload: dict[str, Any], alignment: dict[str, Any]) -> list[str]:
    text = " ".join(
        [
            payload.get("problem", ""),
            payload.get("insight", ""),
            payload.get("angle", ""),
            payload.get("narrative_tension", ""),
            payload.get("payoff", ""),
            payload.get("cta", ""),
        ]
    )
    normalized = _normalize(text)
    flags: list[str] = []
    for item in alignment.get("disallowed_patterns") or []:
        flags.append(f"disallowed_pattern:{item}")
    commodity_triggers = {
        "acredite em voce": "coach_barato",
        "segredo": "copy_inflada",
        "viral": "commodity",
        "mude sua vida": "promise_inflation",
        "antes que seja tarde": "fear_inflation",
    }
    for fragment, label in commodity_triggers.items():
        if fragment in normalized and label not in flags:
            flags.append(label)
    if len(_keywords(topic_seed)) < 2:
        flags.append("topic_seed_fraco")
    return flags


def _clarity_flags(payload: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    for key in ("problem", "insight", "angle", "narrative_tension", "payoff"):
        value = _clean(payload.get(key))
        if len(value) < 24:
            flags.append(f"{key}_curto")
    if len(_clean(payload.get("cta"))) < 18:
        flags.append("cta_curto")
    return flags


def _caption_comprehension_gate(payload: dict[str, Any], anti_commodity_flags: list[str], clarity_flags: list[str]) -> dict[str, Any]:
    text = " ".join(
        [
            payload.get("problem", ""),
            payload.get("insight", ""),
            payload.get("angle", ""),
            payload.get("payoff", ""),
            payload.get("cta", ""),
        ]
    )
    normalized = _normalize(text)
    rejection_reasons: list[str] = []

    if any(flag in anti_commodity_flags for flag in {"coach_barato", "copy_inflada", "commodity", "promise_inflation"}):
        rejection_reasons.append("commodity_or_coach_detectado")
    if len([flag for flag in clarity_flags if flag.endswith("_curto")]) >= 2:
        rejection_reasons.append("texto_curto_demais_para_compreensao")
    if normalized.count("muito") >= 2:
        rejection_reasons.append("copy_inflada")
    if "segredo" in normalized:
        rejection_reasons.append("pattern_cliche")
    if not any(term in normalized for term in {"problema", "custo", "clareza", "estrutura", "resultado", "direcao"}):
        rejection_reasons.append("abstracao_excessiva")

    return {
        "approved": not rejection_reasons,
        "rejection_reasons": rejection_reasons,
        "blocked_abstract_text": "abstracao_excessiva" in rejection_reasons,
        "blocked_cheap_coach": "commodity_or_coach_detectado" in rejection_reasons,
        "blocked_commodity": "commodity_or_coach_detectado" in rejection_reasons,
        "blocked_inflated_copy": "copy_inflada" in rejection_reasons,
    }


def _anti_cliche_policy(alignment: dict[str, Any], anti_commodity_flags: list[str]) -> dict[str, Any]:
    violations = list(alignment.get("disallowed_patterns") or [])
    if "copy_inflada" in anti_commodity_flags:
        violations.append("copy_inflada")
    return {
        "ok": not violations,
        "violations": violations,
        "policy_version": "anti_cliche_v2",
    }


def _pattern_interrupt_policy(domain: str, payload: dict[str, Any]) -> dict[str, Any]:
    family = payload.get("hook_family") or "discipline_reframe"
    allowed_families = {
        "misread_reality",
        "hidden_cost",
        "identity_break",
        "discipline_reframe",
    }
    approved = family in allowed_families
    return {
        "ok": approved,
        "hook_family": family,
        "pattern_interrupt_kind": family if approved else "discipline_reframe",
        "approved": approved,
        "reason": "pattern interrupt auditável sem sensacionalismo",
        "domain": domain,
    }


def _brand_ontology(topic_seed: str) -> dict[str, Any]:
    lexicon = get_brand_lexicon()
    examples = examples_context(topic_seed)
    return {
        "lexicon": list(lexicon.get("semantic_anchors") or []),
        "anti_lexicon": list(lexicon.get("disallowed_patterns") or []),
        "voice": list(lexicon.get("brand_voice") or []),
        "anti_voice": list(lexicon.get("anti_voice") or []),
        "approved_examples": list(examples.get("approved_examples") or []),
        "rejected_examples": list(examples.get("rejected_examples") or []),
    }


def build_planner_editorial_soberano_v2(
    *,
    topic_seed: str,
    signal_context: dict[str, Any] | None = None,
    brand_context: dict[str, Any] | None = None,
    format_hint: str | None = None,
) -> dict[str, Any]:
    signal_context = dict(signal_context or {})
    brand_context = dict(brand_context or {})
    lexicon = get_brand_lexicon()

    topic_seed = _clean(topic_seed or "clareza, disciplina e direção")
    if _normalize(topic_seed) in WEAK_INPUTS:
        topic_seed = "clareza, disciplina e direção"

    domain = _domain(topic_seed)
    payload = _deterministic_editorial_payload(topic_seed, domain, format_hint)
    alignment = scan_brand_alignment(" ".join(str(v) for v in payload.values()), lexicon)
    anti_commodity_flags = _anti_commodity_flags(topic_seed, payload, alignment)
    clarity_flags = _clarity_flags(payload)
    caption_gate = _caption_comprehension_gate(payload, anti_commodity_flags, clarity_flags)
    anti_cliche_policy = _anti_cliche_policy(alignment, anti_commodity_flags)
    pattern_interrupt_policy = _pattern_interrupt_policy(domain, payload)

    memory_context = {}
    for source in (brand_context, signal_context):
        for key in (
            "ace_content_history",
            "ace_candidate_posts",
            "recent_posts",
            "recent_content",
            "episodic_performance_memory",
            "experiment_registry",
            "performance_context",
        ):
            if source.get(key) is not None:
                memory_context[key] = source.get(key)

    serial_v1 = build_serial_continuity_engine_v1(
        topic_seed=topic_seed,
        hook=payload["problem"],
        angle=payload["angle"],
        sequel_potential=payload["sequel_potential"],
        memory_context=memory_context,
        series_name=brand_context.get("series_name") or "Liberta a Verdade",
    )
    serial_continuity = {
        "series_name": serial_v1.get("series_name"),
        "linked_series_candidate": bool(serial_v1.get("sequel_candidate")),
        "next_episode_seed": serial_v1.get("next_episode_seed"),
        "episode_index_hint": serial_v1.get("episode_index_hint"),
        "continuity_reason": serial_v1.get("continuity_reason"),
        "continuity_confidence": serial_v1.get("continuity_confidence"),
        "carryover_hook": serial_v1.get("carryover_hook"),
        "carryover_problem": serial_v1.get("carryover_problem"),
        "carryover_payoff": serial_v1.get("carryover_payoff"),
        "source_mode": serial_v1.get("source_mode"),
    }

    distribution_pack = build_distribution_seriality_pack(
        topic_seed=topic_seed,
        format_recommendation=payload["format_recommendation"],
        serial_continuity=serial_continuity,
        performance_context=memory_context.get("performance_context"),
        signal_context=signal_context,
    )

    return {
        "ok": True,
        "planner_selected": "planner_editorial_soberano_v2",
        "planner_version": PLANNER_VERSION,
        "planner_mode": "deterministic",
        "deterministic": True,
        "deterministic_path": True,
        "topic_seed": topic_seed,
        "problem": payload["problem"],
        "insight": payload["insight"],
        "angle": payload["angle"],
        "hook_family": payload["hook_family"],
        "hook": payload["hook"],
        "headline": payload["headline"],
        "body": payload["body"],
        "support_points": list(payload["support_points"]),
        "narrative_tension": payload["narrative_tension"],
        "payoff": payload["payoff"],
        "CTA": payload["cta"],
        "cta": payload["cta"],
        "format_recommendation": payload["format_recommendation"],
        "sequel_potential": payload["sequel_potential"],
        "perceived_value_hypothesis": _perceived_value_hypothesis(domain),
        "anti_commodity_flags": anti_commodity_flags,
        "clarity_flags": clarity_flags,
        "continuation_candidate": bool(serial_continuity["linked_series_candidate"]),
        "brand_ontology": _brand_ontology(topic_seed),
        "caption_comprehension_gate": caption_gate,
        "caption_gate": caption_gate,
        "anti_cliche_policy": anti_cliche_policy,
        "pattern_interrupt_policy": pattern_interrupt_policy,
        "serial_continuity": serial_continuity,
        "distribution_context": distribution_pack,
        "distribution_pack": distribution_pack,
        "official_path_quality_state": (
            "approved"
            if caption_gate["approved"] and not anti_commodity_flags
            else "needs_rewrite"
        ),
        "fallback_flags": ["deterministic_path"],
        "notes": [
            "planner_selected=planner_editorial_soberano_v2",
            "planner_mode=deterministic",
            f"caption_gate_approved={caption_gate['approved']}",
            f"linked_series_candidate={serial_continuity['linked_series_candidate']}",
            f"distribution_source_mode={distribution_pack['source_mode']}",
        ],
    }
