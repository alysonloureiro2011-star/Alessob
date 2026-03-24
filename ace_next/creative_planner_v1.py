from __future__ import annotations

import re
import unicodedata
from typing import Any

from .brand_ontology import get_brand_ontology, ontology_lexicon_hits
from .caption_comprehension_gate import evaluate_caption_comprehension
from .pattern_interrupt_policy import resolve_pattern_interrupt_policy
from .serial_continuity_engine import build_serial_continuity


VALID_FORMATS = {"image", "carousel", "story", "reel"}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value or "")
        if not unicodedata.combining(char)
    )


def _normalize(value: str) -> str:
    return _strip_accents(_clean_text(value)).lower()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", _normalize(value))


def _keywords(topic_seed: str) -> list[str]:
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", topic_seed.lower())
    stopwords = {
        "a", "ao", "aos", "as", "às", "com", "como", "da", "das", "de", "do", "dos",
        "e", "é", "em", "mais", "menos", "na", "nas", "no", "nos", "o", "os", "ou",
        "para", "por", "que", "se", "sem", "sobre", "um", "uma", "uns", "umas",
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
    domains = {
        "faith": ["fé", "deus", "oração", "propósito", "jesus", "bíblia", "espiritual"],
        "emotion": ["ansiedade", "medo", "mente", "emocional", "angústia", "paz"],
        "discipline": ["disciplina", "foco", "consistência", "execução", "direção", "clareza"],
        "branding": ["marca", "conteúdo", "instagram", "autoridade", "posicionamento", "comunicação"],
        "prosperity": ["prosperidade", "dinheiro", "escassez", "riqueza", "financeiro"],
    }
    best = "discipline"
    best_hits = 0
    for domain, terms in domains.items():
        hits = sum(1 for term in terms if _normalize(term) in text)
        if hits > best_hits:
            best_hits = hits
            best = domain
    return best


def _family_bundle(domain: str) -> dict[str, str]:
    if domain == "faith":
        return {
            "hook_family": "misread_reality",
            "narrative_tension": "convicção sem estrutura perde força",
            "payoff": "fé vira prática, não impulso",
        }
    if domain == "emotion":
        return {
            "hook_family": "hidden_cost",
            "narrative_tension": "reação automática amplia o desgaste",
            "payoff": "clareza reduz peso interno desnecessário",
        }
    if domain == "branding":
        return {
            "hook_family": "identity_break",
            "narrative_tension": "volume sem identidade suga autoridade",
            "payoff": "posicionamento ganha nitidez e valor percebido",
        }
    if domain == "prosperity":
        return {
            "hook_family": "discipline_reframe",
            "narrative_tension": "pressa sem base sabota construção",
            "payoff": "resultado passa a responder a processo",
        }
    return {
        "hook_family": "discipline_reframe",
        "narrative_tension": "boa intenção sem eixo se dispersa",
        "payoff": "execução ganha forma e direção",
    }


def _choose_format(domain: str, format_hint: str | None) -> str:
    hint = (format_hint or "").strip().lower()
    if hint in VALID_FORMATS:
        return hint
    if domain in {"branding", "prosperity"}:
        return "carousel"
    if domain == "emotion":
        return "reel"
    return "image"


def _compose_plan(topic_seed: str, domain: str) -> dict[str, Any]:
    words = _keywords(topic_seed)
    primary = words[0] if len(words) > 0 else "clareza"
    secondary = words[1] if len(words) > 1 else "disciplina"
    tertiary = words[2] if len(words) > 2 else "direção"

    bundle = _family_bundle(domain)

    if domain == "faith":
        problem = f"muita gente quer viver {primary}, mas tenta sustentar isso sem {secondary}"
        insight = f"{primary.capitalize()} sem {secondary} vira emoção passageira; com estrutura, vira postura"
        angle = f"{topic_seed} precisa sair do discurso e entrar em prática sustentada"
        hook = (
            f"Muita gente chama isso de falta de fé, mas o erro costuma ser outro: "
            f"tentar sustentar {primary} sem construir {secondary}."
        )
        headline = f"Sem {secondary}, até {primary} perde força no cotidiano."
        body = (
            f"O problema não está em sentir pouco. Está em organizar mal. Quando {primary} fica solta, "
            f"ela depende do humor do dia. Quando {secondary} entra, a decisão ganha lastro. "
            f"E quando {tertiary} assume comando, o que antes parecia inspiração começa a virar prática real."
        )
    elif domain == "emotion":
        problem = f"{primary} cresce quando a mente reage antes de ler a situação com {secondary}"
        insight = f"nem todo peso emocional é o problema principal; às vezes o dano maior está na leitura ruim"
        angle = f"{topic_seed} deve ser tratado com leitura e eixo, não com reação automática"
        hook = (
            f"Nem sempre o peso de {primary} é o centro da questão. "
            f"Muitas vezes o desgaste explode porque tudo está sendo lido sem {secondary}."
        )
        headline = f"Sem {secondary}, {primary} ocupa o dia inteiro."
        body = (
            f"Quando falta {secondary}, qualquer ruído parece urgência. "
            f"Quando {tertiary} entra, a mente volta a diferenciar pressão real de reação automática. "
            f"O resultado não é perfeição instantânea. É menos desgaste, mais lucidez e resposta melhor."
        )
    elif domain == "branding":
        problem = f"{primary} sem identidade e sem {secondary} vira só mais uma peça no ruído"
        insight = f"marca forte não nasce de volume; nasce de hierarquia, recorte e valor percebido"
        angle = f"{topic_seed} precisa sair da estética de produção e entrar em lógica de posicionamento"
        hook = (
            f"O problema raramente é falta de conteúdo. O problema é produzir {primary} sem {secondary}, "
            f"sem recorte e sem uma leitura clara de {tertiary}."
        )
        headline = f"Sem {secondary}, {primary} parece só mais do mesmo."
        body = (
            f"Marca não cresce com excesso de postagem. Cresce quando a mensagem tem eixo, "
            f"quando a forma reforça a ideia e quando o público percebe valor rápido. "
            f"É isso que separa presença editorial de feed commodity."
        )
    elif domain == "prosperity":
        problem = f"{primary} buscada com pressa e sem {secondary} vira expectativa, não construção"
        insight = f"resultado responde melhor a processo previsível do que a ansiedade por avanço"
        angle = f"{topic_seed} só ganha consistência quando a base é estruturada"
        hook = (
            f"O travamento quase nunca nasce da falta de vontade. "
            f"Na maioria das vezes ele nasce de buscar {primary} sem construir {secondary}."
        )
        headline = f"Sem {secondary}, {primary} vira só expectativa."
        body = (
            f"Resultado não respeita ansiedade. Respeita base. "
            f"Quando {secondary} sustenta o processo e {tertiary} organiza prioridade, "
            f"o tema sai do território abstrato e entra na execução concreta."
        )
    else:
        problem = f"{primary} sem {secondary} perde forma antes de virar resultado"
        insight = f"ideia boa sozinha não sustenta mudança; ela precisa de estrutura, repetição e leitura"
        angle = f"{topic_seed} melhora quando sai da frase bonita e entra em critério"
        hook = (
            f"O que mais trava resultado normalmente não é falta de esforço. "
            f"É tentar sustentar {primary} sem {secondary}, como se intenção sozinha bastasse."
        )
        headline = f"Sem {secondary}, {primary} perde força antes de virar resultado."
        body = (
            f"Ideia boa sozinha não segura consistência. Ela precisa de {secondary} para ganhar forma "
            f"e de {tertiary} para não se perder no meio do caminho. "
            f"Quando isso acontece, o tema deixa de soar abstrato e começa a servir para decisão real."
        )

    support_points = [
        f"{primary.capitalize()} sem base vira intenção solta.",
        f"{secondary.capitalize()} sustenta repetição quando o entusiasmo cai.",
        f"{tertiary.capitalize()} protege prioridade e reduz ruído.",
    ]

    cta = (
        "Salve para revisar antes da próxima decisão e envie para alguém que precisa de "
        "mais critério e menos ruído."
    )

    return {
        "problem": problem,
        "insight": insight,
        "angle": angle,
        "hook": hook,
        "headline": headline,
        "body": body,
        "support_points": support_points,
        "cta": cta,
        "hook_family": bundle["hook_family"],
        "narrative_tension": bundle["narrative_tension"],
        "payoff": bundle["payoff"],
    }


def build_creative_plan_v1(
    topic_seed: str,
    signal_context: dict | None = None,
    brand_context: dict | None = None,
    format_hint: str | None = None,
) -> dict[str, Any]:
    signal_context = dict(signal_context or {})
    ontology = dict(brand_context or get_brand_ontology())

    topic_seed = _clean_text(topic_seed or "clareza, disciplina e direção")
    if not topic_seed or _normalize(topic_seed) in {"teste", "teste real", "oi", "hello", "123"}:
        topic_seed = "clareza, disciplina e direção"

    domain = _detect_domain(topic_seed)
    plan_core = _compose_plan(topic_seed, domain)
    format_recommendation = _choose_format(domain, format_hint)

    caption_gate = evaluate_caption_comprehension(
        headline=plan_core["headline"],
        hook=plan_core["hook"],
        body=plan_core["body"],
        cta=plan_core["cta"],
        ontology=ontology,
    )

    pattern_policy = resolve_pattern_interrupt_policy(
        format_type=format_recommendation,
        hook=plan_core["hook"],
        headline=plan_core["headline"],
        body=plan_core["body"],
    )

    draft_plan = {
        "topic_seed": topic_seed,
        "series_name": ontology.get("brand_name"),
        "format_recommendation": format_recommendation,
        **plan_core,
    }

    serial_continuity = build_serial_continuity(
        creative_plan=draft_plan,
        recent_memory=signal_context.get("recent_memory"),
    )

    full_text = " ".join(
        [
            plan_core["headline"],
            plan_core["hook"],
            plan_core["body"],
            plan_core["cta"],
            *plan_core["support_points"],
        ]
    )

    brand_lexicon_hits = ontology_lexicon_hits(full_text, ontology)

    risk_flags = list(caption_gate.get("flags") or [])
    if not pattern_policy.get("allowed"):
        risk_flags.append("pattern_interrupt_blocked")

    result = {
        "ok": True,
        "topic_seed": topic_seed,
        "problem": plan_core["problem"],
        "insight": plan_core["insight"],
        "angle": plan_core["angle"],
        "hook": plan_core["hook"],
        "headline": plan_core["headline"],
        "body": plan_core["body"],
        "support_points": list(plan_core["support_points"]),
        "cta": plan_core["cta"],
        "format_recommendation": format_recommendation,
        "hook_family": plan_core["hook_family"],
        "narrative_tension": plan_core["narrative_tension"],
        "payoff": plan_core["payoff"],
        "series_name": serial_continuity.get("series_name"),
        "sequel_potential": serial_continuity.get("continuation_type"),
        "brand_lexicon_hits": brand_lexicon_hits,
        "risk_flags": risk_flags,
        "notes": [
            "planner_selected=creative_planner_v1",
            "planner_generation_ok=true",
            f"caption_gate_result={caption_gate.get('approved')}",
            f"pattern_interrupt_policy_result={pattern_policy.get('allowed')}",
            f"serial_continuity_result={serial_continuity.get('continuation_type')}",
        ],
        "caption_gate": caption_gate,
        "pattern_interrupt_policy": pattern_policy,
        "serial_continuity": serial_continuity,
        "approved_example_ids": list(ontology.get("approved_example_ids", [])),
        "rejected_example_ids": list(ontology.get("rejected_example_ids", [])),
    }
    return result


def run_editorial_brain_selftest() -> dict[str, Any]:
    planner_demo = build_creative_plan_v1("ansiedade, disciplina e direção")
    weak_gate = evaluate_caption_comprehension(
        headline="Acredite em você",
        hook="Descubra o segredo para sua vida mudar agora",
        body="Tudo pode mudar.",
        cta="Comente aqui",
        ontology=get_brand_ontology(),
    )
    strong_gate = evaluate_caption_comprehension(
        headline=planner_demo["headline"],
        hook=planner_demo["hook"],
        body=planner_demo["body"],
        cta=planner_demo["cta"],
        ontology=get_brand_ontology(),
    )
    pattern_demo = resolve_pattern_interrupt_policy(
        format_type=planner_demo["format_recommendation"],
        hook=planner_demo["hook"],
        headline=planner_demo["headline"],
        body=planner_demo["body"],
    )
    serial_demo = build_serial_continuity(planner_demo)

    return {
        "ok": True,
        "planner_demo": planner_demo,
        "weak_gate": weak_gate,
        "strong_gate": strong_gate,
        "pattern_demo": pattern_demo,
        "serial_demo": serial_demo,
    }
