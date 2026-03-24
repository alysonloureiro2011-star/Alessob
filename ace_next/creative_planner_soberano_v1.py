from __future__ import annotations

import re
import unicodedata
from typing import Any

from .brand_lexicon import get_brand_lexicon, scan_brand_alignment
from .editorial_critic_v1 import evaluate_editorial_critic


VALID_FORMATS = {"image", "carousel", "story", "reel"}


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
        return "reel"
    if domain in {"branding", "prosperity"}:
        return "carousel"
    return "image"


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
            "body": f"Resultado não respeita ansiedade. Respeita base. Quando {secondary} sustenta o processo e {tertiary} organiza prioridade, o tema deixa de soar abstrato e começa a responder a execução real.",
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
    if _normalize(topic_seed) in {"", "teste", "teste real", "oi", "hello", "123"}:
        topic_seed = "clareza, disciplina e direção"

    domain = _detect_domain(topic_seed)
    payload = _compose_editorial_payload(topic_seed, domain)
    format_recommendation = _choose_format(domain, format_hint)
    body = payload["body"]
    support_points = list(payload["support_points"])
    full_text = " ".join([payload["headline"], payload["hook"], body, payload["cta"], *support_points])

    alignment = scan_brand_alignment(full_text, lexicon)
    critic = evaluate_editorial_critic(payload, lexicon)

    sequel_potential = "high" if format_recommendation in {"reel", "carousel"} else "medium"
    series_name = brand_context.get("series_name") or lexicon["brand_name"]

    plan = {
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
        "format_recommendation": format_recommendation,
        "sequel_potential": sequel_potential,
        "series_name": series_name,
        "brand_fit_signals": alignment["semantic_anchors"] + alignment["approved_language_patterns"][:2],
        "anti_generic_signals": [
            "ângulo utilitário e não ornamental",
            "headline causal em vez de slogan",
            "hook com custo, erro ou contraste de leitura",
        ],
        "anti_commodity_signals": [
            "sem promessa apelativa",
            "CTA útil em vez de mendigado",
            "sem gatilho barato de urgência",
        ],
        "tone_controls": [
            "clareza antes de volume",
            "autoridade sem arrogância",
            "naturalidade sem frase inflada",
            "tensão ética sem sensacionalismo",
        ],
        "rejected_patterns": list(lexicon["disallowed_patterns"]),
        "critic": critic,
        "notes": [
            "planner_selected=creative_planner_soberano_v1",
            "planner_generation_ok=true",
            f"editorial_critic_approved={critic.get('approved')}",
        ],
    }
    return plan


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
        "brand_fit_signals": [],
        "anti_generic_signals": [],
        "anti_commodity_signals": [],
        "tone_controls": [],
        "rejected_patterns": get_brand_lexicon()["disallowed_patterns"],
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
    return {"ok": True, "approved_example": approved, "rejected_example": rejected_like}
