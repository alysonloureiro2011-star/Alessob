import os
import requests
import random
import datetime


def env(name, default=None):
    return os.environ.get(name, default)


ACE_LLM_PROVIDER = str(env("ACE_LLM_PROVIDER", "auto")).lower()

GEMINI_KEY = env("GEMINI_KEY") or env("GEMINI_API_KEY")
GEMINI_MODEL = env("GEMINI_MODEL", "gemini-2.5-flash-lite")

OPENAI_KEY = env("OPENAI_API_KEY")
OPENAI_MODEL = env("OPENAI_MODEL", "gpt-4.1-mini")


# --------------------------------------------
# GEMINI
# --------------------------------------------

def call_gemini(prompt):

    if not GEMINI_KEY:
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

    try:

        r = requests.post(url, json=payload, timeout=60)

        if r.status_code != 200:
            return None

        data = r.json()

        candidates = data.get("candidates", [])

        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])

        text = "\n".join([p.get("text", "") for p in parts])

        return text.strip()

    except Exception:
        return None


# --------------------------------------------
# OPENAI
# --------------------------------------------

def call_openai(prompt):

    if not OPENAI_KEY:
        return None

    headers = {
        "Authorization": f"Bearer {OPENAI_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENAI_MODEL,
        "input": prompt
    }

    try:

        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
            timeout=60
        )

        if r.status_code != 200:
            return None

        data = r.json()

        if "output_text" in data:
            return data["output_text"]

        output = data.get("output", [])

        texts = []

        for item in output:
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    texts.append(c.get("text", ""))

        return "\n".join(texts).strip()

    except Exception:
        return None


# --------------------------------------------
# LLM ROUTER
# --------------------------------------------

def generate_with_llm(prompt):

    provider = ACE_LLM_PROVIDER

    if provider == "gemini":

        text = call_gemini(prompt)

        if text:
            return text

    if provider == "openai":

        text = call_openai(prompt)

        if text:
            return text

    if provider == "auto":

        text = call_gemini(prompt)

        if text:
            return text

        text = call_openai(prompt)

        if text:
            return text

    return None


# --------------------------------------------
# HOOK
# --------------------------------------------

def generate_hook(trend):

    prompt = f"""
Crie um hook curto para Instagram.

Tema: {trend}

Regras:
até 12 palavras
forte
curioso
sem emoji
sem hashtags
retorne apenas a frase
"""

    text = generate_with_llm(prompt)

    if text:

        line = text.split("\n")[0]

        return line.strip()

    hooks = [
        f"O erro que todo mundo comete quando fala de {trend}",
        f"A verdade que ninguém aceita sobre {trend}",
        f"O detalhe que destrói {trend} e quase ninguém percebe",
        f"Por que {trend} está enganando tanta gente",
        f"O que realmente está acontecendo com {trend}",
    ]

    return random.choice(hooks)


# --------------------------------------------
# BODY
# --------------------------------------------

def generate_body(trend, style, content_type):

    prompt = f"""
Escreva um conteúdo para Instagram.

Tema: {trend}
Estilo: {style}
Formato: {content_type}

Regras:

linguagem humana
claro
sem clichê
sem emoji
sem hashtags
ritmo natural

Para carrossel escreva em blocos curtos.
Para reels escreva como fala natural.
"""

    text = generate_with_llm(prompt)

    if text:
        return text.strip()

    fallback = [

        "Disciplina sem direção vira desgaste.",

        "Prosperidade sem disciplina vira ilusão.",

        "Muita gente quer resultado sem sustentar o processo.",

        "Constância silenciosa vence intensidade passageira.",

        "A diferença entre quem vence e quem tenta está na repetição.",

        "Salve isso para lembrar quando quiser desistir."

    ]

    if content_type == "carrossel":
        return "\n\n".join(fallback)

    return " ".join(fallback)


# --------------------------------------------
# BUILD PACKAGE
# --------------------------------------------

def build_content_package(trend, style, content_type):

    hook = generate_hook(trend)

    body = generate_body(trend, style, content_type)

    caption = f"{hook}\n\n{body}"

    caption = caption[:2200]

    return {

        "hook": hook,

        "body": body,

        "caption": caption,

        "trend": trend,

        "style": style,

        "content_type": content_type,

        "created_at": datetime.datetime.utcnow().isoformat()

    }
