import os
import json
import random
import datetime
from pathlib import Path

import requests


# ==========================================================
# CONFIG
# ==========================================================

BASE_DIR = Path(__file__).resolve().parents[2]
MEMORY_DIR = BASE_DIR / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

CREATIVE_BRAIN_MEMORY_PATH = MEMORY_DIR / "creative_brain_memory.json"


def env(name, default=None):
    return os.environ.get(name, default)


ACE_LLM_PROVIDER = str(env("ACE_LLM_PROVIDER", "auto")).strip().lower()

GEMINI_KEY = env("GEMINI_KEY") or env("GEMINI_API_KEY")
GEMINI_MODEL = str(env("GEMINI_MODEL", "gemini-2.5-flash-lite")).strip()

OPENAI_KEY = env("OPENAI_API_KEY")
OPENAI_MODEL = str(env("OPENAI_MODEL", "gpt-4.1-mini")).strip()

ACE_LLM_DAILY_BUDGET = int(env("ACE_LLM_DAILY_BUDGET", "80"))


# ==========================================================
# MEMORY
# ==========================================================

def load_creative_memory():
    if CREATIVE_BRAIN_MEMORY_PATH.exists():
        try:
            return json.loads(CREATIVE_BRAIN_MEMORY_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass

    return {
        "last_reset_date": str(datetime.date.today()),
        "llm_calls_today": 0,
        "hooks": {},
        "openings": {},
        "ctas": {},
        "history": []
    }


def save_creative_memory(data):
    try:
        CREATIVE_BRAIN_MEMORY_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except Exception:
        pass


CREATIVE_MEMORY = load_creative_memory()


def reset_budget_if_needed():
    today = str(datetime.date.today())
    if CREATIVE_MEMORY.get("last_reset_date") != today:
        CREATIVE_MEMORY["last_reset_date"] = today
        CREATIVE_MEMORY["llm_calls_today"] = 0
        save_creative_memory(CREATIVE_MEMORY)


def can_use_llm():
    reset_budget_if_needed()
    return int(CREATIVE_MEMORY.get("llm_calls_today", 0)) < ACE_LLM_DAILY_BUDGET


def register_llm_call():
    reset_budget_if_needed()
    CREATIVE_MEMORY["llm_calls_today"] = int(CREATIVE_MEMORY.get("llm_calls_today", 0)) + 1
    save_creative_memory(CREATIVE_MEMORY)


def remember_result(trend, style, content_type, hook, opening, cta):
    history = CREATIVE_MEMORY.setdefault("history", [])
    history.append({
        "ts": datetime.datetime.utcnow().isoformat(),
        "trend": trend,
        "style": style,
        "content_type": content_type,
        "hook": hook,
        "opening": opening,
        "cta": cta,
    })
    CREATIVE_MEMORY["history"] = history[-120:]

    if hook:
        CREATIVE_MEMORY.setdefault("hooks", {})
        CREATIVE_MEMORY["hooks"][hook] = CREATIVE_MEMORY["hooks"].get(hook, 0) + 1

    if opening:
        CREATIVE_MEMORY.setdefault("openings", {})
        CREATIVE_MEMORY["openings"][opening] = CREATIVE_MEMORY["openings"].get(opening, 0) + 1

    if cta:
        CREATIVE_MEMORY.setdefault("ctas", {})
        CREATIVE_MEMORY["ctas"][cta] = CREATIVE_MEMORY["ctas"].get(cta, 0) + 1

    save_creative_memory(CREATIVE_MEMORY)


# ==========================================================
# HTTP / LLM
# ==========================================================

def safe_post(url, *, headers=None, json_payload=None, timeout=60):
    try:
        r = requests.post(url, headers=headers, json=json_payload, timeout=timeout)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:4000]}

        return {
            "ok": r.status_code < 400,
            "status_code": r.status_code,
            "data": data,
        }
    except Exception as e:
        return {
            "ok": False,
            "status_code": None,
            "error": str(e),
        }


def call_gemini(prompt):
    if not GEMINI_KEY or not can_use_llm():
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    result = safe_post(url, json_payload=payload, timeout=60)

    if not result.get("ok"):
        return None

    try:
        data = result.get("data", {})
        candidates = data.get("candidates", [])
        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        text = "\n".join([p.get("text", "") for p in parts if p.get("text")]).strip()

        if text:
            register_llm_call()
            return text
        return None
    except Exception:
        return None


def call_openai(prompt):
    if not OPENAI_KEY or not can_use_llm():
        return None

    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": OPENAI_MODEL,
        "input": prompt,
    }

    result = safe_post(
        "https://api.openai.com/v1/responses",
        headers=headers,
        json_payload=payload,
        timeout=60,
    )

    if not result.get("ok"):
        return None

    try:
        data = result.get("data", {})

        if data.get("output_text"):
            register_llm_call()
            return str(data["output_text"]).strip()

        output = data.get("output", [])
        texts = []

        for item in output:
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    texts.append(content.get("text", ""))

        text = "\n".join([t for t in texts if t]).strip()

        if text:
            register_llm_call()
            return text
        return None
    except Exception:
        return None


def query_llm(prompt):
    provider = ACE_LLM_PROVIDER

    if provider == "gemini":
        return call_gemini(prompt)

    if provider == "openai":
        return call_openai(prompt)

    if provider == "auto":
        text = call_gemini(prompt)
        if text:
            return text

        text = call_openai(prompt)
        if text:
            return text

    return None


# ==========================================================
# CONSULTA EXTERNA (MICRO-INSIGHTS)
# ==========================================================

def query_micro_insights(trend, style, content_type):
    prompt = f"""
Responda em português do Brasil.

Tema: {trend}
Estilo: {style}
Formato: {content_type}

Quero apenas material bruto de consulta.
Não escreva post pronto.
Não explique.
Não introduza.
Não comente.

Entregue exatamente assim:

HOOKS:
- frase
- frase
- frase
- frase
- frase

TENSOES:
- frase
- frase
- frase
- frase
- frase

VERDADES:
- frase
- frase
- frase
- frase
- frase

CTAS:
- frase
- frase
- frase

Regras:
- frases curtas
- humanas
- naturais
- fortes
- sem emoji
- sem hashtags
- sem "aqui estão"
- sem "com certeza"
- sem estrutura de aula
- sem mencionar Instagram
""".strip()

    return query_llm(prompt)


def parse_bullets(text, section_name):
    if not text:
        return []

    lines = text.splitlines()
    capture = False
    items = []

    for line in lines:
        raw = line.strip()

        if not raw:
            continue

        if raw.upper().startswith(f"{section_name}:"):
            capture = True
            continue

        if capture and raw.endswith(":") and raw.upper() != f"{section_name}:":
            break

        if capture and raw.startswith("-"):
            item = raw.lstrip("-").strip()
            if item:
                items.append(item)

    return items


# ==========================================================
# PERFIS DE ESTILO
# ==========================================================

def get_style_profile(style):
    style = (style or "").strip().lower()

    profiles = {
        "filosofico": {
            "opening": "Quase ninguém percebe isso no começo.",
            "closing": "No fim, o que parece lento é justamente o que sustenta o que dura.",
            "cta": "Salve isso e releia com calma."
        },
        "provocativo": {
            "opening": "O problema não está onde te disseram.",
            "closing": "E é justamente aí que quase todo mundo se perde.",
            "cta": "Salve isso antes de esquecer."
        },
        "reflexivo": {
            "opening": "Tem coisa que só fica clara depois de muita dor.",
            "closing": "Nem sempre o que pesa é o que destrói. Às vezes é o que revela.",
            "cta": "Salve isso para voltar depois."
        },
        "direto": {
            "opening": "Vou te falar sem enfeite.",
            "closing": "O resto é distração.",
            "cta": "Salve isso e aplique hoje."
        },
        "espiritual": {
            "opening": "Tem batalha que começa muito antes do lado de fora.",
            "closing": "O invisível quase sempre vem antes do visível.",
            "cta": "Salve isso e medite nisso."
        },
    }

    return profiles.get(style, {
        "opening": "Quase ninguém fala disso com clareza.",
        "closing": "No fim, o que sustenta resultado não é pressa. É estrutura.",
        "cta": "Salve isso para lembrar na hora certa."
    })


# ==========================================================
# FALLBACKS SOBERANOS
# ==========================================================

def fallback_hook(trend):
    options = [
        f"O erro que todo mundo comete quando fala de {trend}",
        f"O que realmente está acontecendo com {trend}",
        f"A verdade desconfortável sobre {trend}",
        f"Por que {trend} está enganando tanta gente",
        f"O detalhe que quase ninguém percebe sobre {trend}",
    ]
    return random.choice(options)


def fallback_tension(trend):
    options = [
        f"Muita gente quer o resultado de {trend}, mas rejeita o processo.",
        f"O discurso sobre {trend} ficou bonito demais e honesto de menos.",
        f"As pessoas tratam {trend} como desejo, quando na prática é construção.",
        f"O problema é confundir impulso com constância dentro de {trend}.",
    ]
    return random.choice(options)


def fallback_truth(trend):
    options = [
        f"{trend.capitalize()} não nasce de intensidade curta. Nasce de repetição certa.",
        f"{trend.capitalize()} não depende só de vontade. Depende de direção e constância.",
        f"No fim, {trend} é menos sobre motivação e mais sobre estrutura.",
        f"A parte invisível de {trend} é justamente a que sustenta o resultado visível.",
    ]
    return random.choice(options)


def fallback_cta(style):
    return get_style_profile(style)["cta"]


# ==========================================================
# SCORE / SELEÇÃO
# ==========================================================

def score_phrase(text, trend, style):
    if not text:
        return 0.0

    score = 1.0
    low = text.lower()

    if len(text) < 18:
        score -= 0.12
    if len(text) > 140:
        score -= 0.18

    bad_patterns = [
        "aqui estão",
        "com certeza",
        "opções de conteúdo",
        "instagram",
        "reel",
        "carrossel",
        "bloco 1",
        "explicação",
        "conteúdo para",
        "ideia geral",
    ]

    for bad in bad_patterns:
        if bad in low:
            score -= 0.35

    if trend.lower() in low:
        score += 0.08

    if any(word in low for word in ["verdade", "erro", "quase ninguém", "realmente", "detalhe"]):
        score += 0.08

    if style.lower() in low:
        score += 0.03

    return round(score, 4)


def pick_best(candidates, trend, style, fallback_value):
    cleaned = [c.strip(" -•\t") for c in candidates if c and c.strip()]
    if not cleaned:
        return fallback_value

    ranked = sorted(
        cleaned,
        key=lambda x: score_phrase(x, trend, style),
        reverse=True
    )

    return ranked[0]


# ==========================================================
# COMPOSIÇÃO AUTORAL
# ==========================================================

def build_authorial_text(trend, style, content_type):
    profile = get_style_profile(style)

    insights_raw = query_micro_insights(trend, style, content_type)

    hooks = parse_bullets(insights_raw, "HOOKS")
    tensions = parse_bullets(insights_raw, "TENSOES")
    truths = parse_bullets(insights_raw, "VERDADES")
    ctas = parse_bullets(insights_raw, "CTAS")

    hook = pick_best(hooks, trend, style, fallback_hook(trend))
    tension = pick_best(tensions, trend, style, fallback_tension(trend))
    truth = pick_best(truths, trend, style, fallback_truth(trend))
    cta = pick_best(ctas, trend, style, fallback_cta(style))

    opening = profile["opening"]
    closing = profile["closing"]

    if content_type == "carrossel":
        body = "\n\n".join([
            opening,
            tension,
            truth,
            closing,
            cta
        ])
    else:
        body = " ".join([
            opening,
            tension,
            truth,
            closing,
            cta
        ])

    caption = f"{hook}\n\n{body}".strip()
    caption = caption[:2200]

    remember_result(
        trend=trend,
        style=style,
        content_type=content_type,
        hook=hook,
        opening=opening,
        cta=cta
    )

    return {
        "hook": hook,
        "body": body,
        "caption": caption,
        "trend": trend,
        "style": style,
        "content_type": content_type,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "llm_calls_today": int(CREATIVE_MEMORY.get("llm_calls_today", 0)),
        "llm_daily_budget": ACE_LLM_DAILY_BUDGET,
    }
