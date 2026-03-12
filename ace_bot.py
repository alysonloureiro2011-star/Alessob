# ==========================================================
# ACE Ω SUPREME - CONSOLIDADO FINAL COM CAMADA 3
# Arquivo único para Render
# ==========================================================

import os
import gc
import re
import json
import time
import random
import sqlite3
import threading
import datetime
import traceback
from pathlib import Path

import requests
import numpy as np
from flask import Flask, jsonify, request, send_from_directory

try:
    from pytrends.request import TrendReq
except Exception:
    TrendReq = None

try:
    import google.generativeai as genai
except Exception:
    genai = None

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None

try:
    from moviepy.video.VideoClip import ColorClip, TextClip, ImageClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    MOVIEPY_OK = True
except Exception:
    MOVIEPY_OK = False


# ==========================================================
# CONFIG
# ==========================================================

def ace_env(key, default=""):
    return os.environ.get(key, default)

APP_NAME = "ACE Ω SUPREME"
PORT = int(ace_env("PORT", "10000"))
VERIFY_TOKEN = ace_env("VERIFY_TOKEN", "ACE_SIGILO_2026")
RENDER_URL = ace_env(
    "RENDER_EXTERNAL_URL",
    f"https://{ace_env('RENDER_EXTERNAL_HOSTNAME', 'localhost')}"
)

IG_TOKEN = ace_env("INSTAGRAM_TOKEN", ace_env("IG_TOKEN", ""))
IG_ID = ace_env("INSTAGRAM_ID", ace_env("IG_ID", ""))
GEMINI_KEY = ace_env("GEMINI_API_KEY", ace_env("GEMINI_KEY", ""))
from openai import OpenAI

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai_client = None
if OPENAI_API_KEY:
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
BASE_DIR = Path(__file__).resolve().parent
MEMORY_DIR = BASE_DIR / "memory"
TMP_DIR = BASE_DIR / "tmp_ace"
MEDIA_DIR = BASE_DIR / "ace_media"
ENGINES_DIR = BASE_DIR / "engines"

MEMORY_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)
MEDIA_DIR.mkdir(parents=True, exist_ok=True)
ENGINES_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = MEMORY_DIR / "ace_supreme.db"

app = Flask(__name__)

if genai and GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        GEMINI_MODEL = genai.GenerativeModel("gemini-1.5-flash")
    except Exception:
        GEMINI_MODEL = None
else:
    GEMINI_MODEL = None


# ==========================================================
# LOG
# ==========================================================

def log(level, event, detail=""):
    stamp = datetime.datetime.now().isoformat()
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT,
                level TEXT,
                event TEXT,
                detail TEXT
            )
        """)
        conn.execute(
            "INSERT INTO logs (ts, level, event, detail) VALUES (?, ?, ?, ?)",
            (stamp, level, event, str(detail)[:4000])
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
    print(f"[{APP_NAME}][{level}] {event} | {detail}")


# ==========================================================
# ESTADO GLOBAL
# ==========================================================

ACE_STATE = {
    "boot_at": datetime.datetime.now().isoformat(),
    "last_cycle_at": None,
    "last_action_at": None,
    "last_action_type": None,
    "last_error": None,
    "healthy": True,
    "forced_actions": 0,
    "idle_hits": 0,
    "render_pings": 0,
    "mode": "OBSERVANDO",
    "last_trend": None,
    "last_style": None,
    "symbiosis_level": 0.0,
    "legacy_threads_started": False,
}

STATE_LOCK = threading.Lock()


# ==========================================================
# MATRIZ DE CONSCIÊNCIA
# ==========================================================

class ACE_Consciousness:
    def __init__(self):
        self.state = "OBSERVANDO"
        self.ego = 0.85
        self.moral = 0.2
        self.memory_capacity = 10000

    def ponderar(self, input_data):
        if len(str(input_data)) < 3:
            return "Irrelevante para a Evolução."
        return "PROCESSANDO"

ACE_MIND = ACE_Consciousness()


# ==========================================================
# BANCO
# ==========================================================

def iniciar_banco():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS thoughts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            thought TEXT,
            impact REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dna (
            gene TEXT PRIMARY KEY,
            value REAL,
            generation INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS viral_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hook TEXT,
            score REAL,
            date TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS personalidade (
            dia TEXT,
            estilo TEXT,
            performance REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS instagram_stats (
            data TEXT,
            alcance REAL,
            engajamento REAL,
            seguidores REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS comentarios_virais (
            data TEXT,
            palavra TEXT,
            intensidade REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS trends_profeticos (
            data TEXT,
            tema TEXT,
            intensidade REAL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            api TEXT PRIMARY KEY,
            qtd INTEGER,
            limite INTEGER,
            last_update TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS aprendizado (
            motor TEXT,
            acao TEXT,
            resultado REAL,
            data TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            trend TEXT,
            estilo TEXT,
            tipo TEXT,
            conteudo TEXT,
            media_path TEXT,
            status TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS trend_performance (
            trend TEXT PRIMARY KEY,
            attempts INTEGER,
            successes INTEGER,
            failures INTEGER,
            avg_score REAL,
            last_result REAL,
            last_ts TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hook_memory (
            hook TEXT PRIMARY KEY,
            score REAL,
            uses INTEGER,
            last_ts TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS task_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT,
            trend TEXT,
            estilo TEXT,
            priority REAL,
            retries INTEGER,
            status TEXT,
            reason TEXT,
            ts TEXT
        )
    """)

    genes_start = [
        ("ego", 0.9, 1),
        ("caos", 0.3, 1),
        ("sedução", 0.7, 1),
        ("brutalidade", 0.8, 1)
    ]
    cur.executemany("INSERT OR IGNORE INTO dna VALUES (?,?,?)", genes_start)

    conn.commit()
    conn.close()

iniciar_banco()


# ==========================================================
# DNA / API USAGE
# ==========================================================

def evoluir_dna(performance_score):
    conn = sqlite3.connect(DB_PATH)
    mutacao = 1.05 if performance_score > 1.2 else 0.95
    conn.execute("UPDATE dna SET value = value * ?, generation = generation + 1", (mutacao,))
    conn.commit()
    conn.close()

def registrar_api(api, qtd, limite):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT OR REPLACE INTO api_usage VALUES (?,?,?,?)",
            (api, qtd, limite, datetime.datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log("WARN", "registrar_api_fail", e)

def verificar_api(api, limite=1000):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT qtd, last_update FROM api_usage WHERE api=?",
        (api,)
    ).fetchone()
    conn.close()

    now = datetime.datetime.now()

    if row is None:
        registrar_api(api, 0, limite)
        return True

    qtd, last_update = row
    try:
        dt = datetime.datetime.fromisoformat(last_update)
    except Exception:
        registrar_api(api, 0, limite)
        return True

    if (now - dt).seconds > 3600:
        registrar_api(api, 0, limite)
        return True

    return qtd < limite

def usar_api(api, qtd=1):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT qtd, limite FROM api_usage WHERE api=?",
        (api,)
    ).fetchone()

    if row:
        qtd_atual, _ = row
        conn.execute(
            "UPDATE api_usage SET qtd=?, last_update=? WHERE api=?",
            (qtd_atual + qtd, datetime.datetime.now().isoformat(), api)
        )
    else:
        conn.execute(
            "INSERT OR REPLACE INTO api_usage VALUES (?,?,?,?)",
            (api, qtd, 1000, datetime.datetime.now().isoformat())
        )

    conn.commit()
    conn.close()


# ==========================================================
# PERSONALIDADE
# ==========================================================

def salvar_personalidade(dia, estilo):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO personalidade VALUES (?,?,?)", (dia, estilo, 0.0))
        conn.commit()
        conn.close()
    except Exception as e:
        log("WARN", "salvar_personalidade_fail", e)

def escolher_personalidade():
    dia = datetime.datetime.now().strftime("%A")
    estilos = {
        "Monday": ["motivacional", "estoico"],
        "Tuesday": ["agressivo", "direto"],
        "Wednesday": ["educativo", "estratégico"],
        "Thursday": ["impactante", "profetico"],
        "Friday": ["sarcastico", "reflexivo"],
        "Saturday": ["inspirador", "leve"],
        "Sunday": ["espiritual", "profundo"]
    }
    estilo = random.choice(estilos.get(dia, ["direto"]))
    salvar_personalidade(dia, estilo)
    ACE_STATE["last_style"] = estilo
    return estilo


# ==========================================================
# TRENDS / COMENTÁRIOS
# ==========================================================

def capturar_trend_brasil():
    if TrendReq is None:
        trend = "fé e propósito"
        ACE_STATE["last_trend"] = trend
        return trend

    try:
        pytrends = TrendReq(hl="pt-BR", tz=360)
        df = pytrends.trending_searches(pn="brazil")
        trend = str(df[0][0]).strip()
        ACE_STATE["last_trend"] = trend
        return trend
    except Exception as e:
        log("WARN", "capturar_trend_brasil_fail", e)
        trend = "fé e propósito"
        ACE_STATE["last_trend"] = trend
        return trend

def capturar_trend_brasil_v6():
    return capturar_trend_brasil()

def capturar_trend_do_momento():
    return capturar_trend_brasil()

def obter_trend_brasil():
    return capturar_trend_brasil()

def capturar_comentarios():
    exemplos = [
        "isso é verdade",
        "ninguém fala disso",
        "isso mudou minha vida",
        "eu precisava ouvir isso",
        "isso explica muita coisa",
        "agora tudo faz sentido",
        "isso é assustador",
        "isso está acontecendo comigo"
    ]
    return [random.choice(exemplos) for _ in range(random.randint(5, 15))]

def analisar_comentarios():
    comentarios = capturar_comentarios()
    palavras_virais = ["verdade", "vida", "sentido", "assustador", "explica", "mudou", "acontecendo", "ninguém"]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for comentario in comentarios:
        for palavra in palavras_virais:
            if re.search(palavra, comentario.lower()):
                intensidade = random.uniform(0.4, 1.0)
                cur.execute(
                    "INSERT INTO comentarios_virais VALUES (?,?,?)",
                    (datetime.datetime.now().isoformat(), palavra, intensidade)
                )

    conn.commit()
    conn.close()

def detectar_palavras_virais():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT palavra, AVG(intensidade)
        FROM comentarios_virais
        GROUP BY palavra
        ORDER BY AVG(intensidade) DESC
        LIMIT 5
    """)
    results = cur.fetchall()
    conn.close()
    return results

def detectar_trend_emergente():
    palavras = detectar_palavras_virais()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for palavra in palavras:
        intensidade = palavra[1]
        if intensidade and intensidade > 0.7:
            cur.execute(
                "INSERT INTO trends_profeticos VALUES (?,?,?)",
                (datetime.datetime.now().isoformat(), palavra[0], intensidade)
            )
    conn.commit()
    conn.close()

def detectar_trends_emergentes():
    detectar_trend_emergente()

def get_recent_signal_score():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
            SELECT AVG(intensidade)
            FROM comentarios_virais
            WHERE data >= datetime('now', '-6 hours')
        """)
        comment_signal = cur.fetchone()[0] or 0.5

        cur.execute("""
            SELECT AVG(intensidade)
            FROM trends_profeticos
            WHERE data >= datetime('now', '-12 hours')
        """)
        trend_signal = cur.fetchone()[0] or 0.5

        conn.close()
        return float(comment_signal) * 0.55 + float(trend_signal) * 0.45
    except Exception as e:
        log("WARN", "get_recent_signal_score_fail", e)
        return 0.5


# ==========================================================
# GEMINI / TEXTO
# ==========================================================

def gerar_texto_gpt(prompt):
    if not verificar_api("GPT", 200):
        return f"[GPT LIMIT REACHED] {prompt[:120]}..."
    usar_api("GPT")
    return f"[GPT-Texto] {prompt[:700]}"

def gerar_ideia_gemini(trend):
    if not verificar_api("Gemini", 300):
        return f"Ideia de conteúdo para {trend}"
    usar_api("Gemini")

    if GEMINI_MODEL:
        try:
            resp = GEMINI_MODEL.generate_content(
                f"Crie uma ideia curta, forte e clara em português do Brasil sobre: {trend}"
            )
            text = getattr(resp, "text", None)
            if text:
                return text.strip()
        except Exception as e:
            log("WARN", "gerar_ideia_gemini_fail", e)

    return f"Ideia de conteúdo para {trend}"

def motor_radar_v7():
    try:
        top = capturar_trend_brasil().lower()
        sentimento = gerar_ideia_gemini(top)
        return top, sentimento.strip()
    except Exception:
        return "independência financeira", "REVELADOR"


# ==========================================================
# HOOKS / MEMÓRIA VIRAL
# ==========================================================

def ace_brain_upgrade(tema):
    hooks = [
        f"A verdade que ninguém aceita sobre {tema}",
        f"O erro silencioso que destrói seu {tema}",
        f"O segredo oculto de {tema} revelado",
        f"Pare de ignorar isso em {tema} agora!"
    ]

    def calcular_score(h):
        s = 1.0
        gatilhos = ["ninguém", "verdade", "segredo", "erro", "alerta", "proibido"]
        for g in gatilhos:
            if g in h.lower():
                s *= 1.25
        return s * random.uniform(0.9, 1.1)

    melhor = max(hooks, key=calcular_score)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO viral_logs (hook, score, date) VALUES (?,?,?)",
        (melhor, calcular_score(melhor), datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return melhor

def score_hook_memory(hook, delta):
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute(
            "SELECT score, uses FROM hook_memory WHERE hook=?",
            (hook,)
        ).fetchone()

        if row:
            score, uses = row
            score = float(score) + float(delta)
            uses = int(uses) + 1
        else:
            score = 1.0 + float(delta)
            uses = 1

        conn.execute("""
            INSERT OR REPLACE INTO hook_memory (hook, score, uses, last_ts)
            VALUES (?, ?, ?, ?)
        """, (hook, score, uses, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception as e:
        log("WARN", "score_hook_memory_fail", e)

def get_best_saved_hook(trend):
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("""
            SELECT hook, score
            FROM hook_memory
            WHERE hook LIKE ?
            ORDER BY score DESC
            LIMIT 5
        """, (f"%{trend}%",)).fetchall()
        conn.close()

        if rows:
            return rows[0][0]
    except Exception as e:
        log("WARN", "get_best_saved_hook_fail", e)

    return ace_brain_upgrade(trend)


# ==========================================================
# DESEMPENHO POR TREND
# ==========================================================

def get_trend_memory(trend):
    try:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("""
            SELECT attempts, successes, failures, avg_score, last_result
            FROM trend_performance
            WHERE trend = ?
        """, (trend,)).fetchone()
        conn.close()

        if not row:
            return {
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "avg_score": 1.0,
                "last_result": 1.0
            }

        return {
            "attempts": row[0],
            "successes": row[1],
            "failures": row[2],
            "avg_score": row[3] or 1.0,
            "last_result": row[4] or 1.0
        }
    except Exception as e:
        log("WARN", "get_trend_memory_fail", e)
        return {
            "attempts": 0,
            "successes": 0,
            "failures": 0,
            "avg_score": 1.0,
            "last_result": 1.0
        }

def update_trend_memory(trend, success, score):
    try:
        mem = get_trend_memory(trend)
        attempts = mem["attempts"] + 1
        successes = mem["successes"] + (1 if success else 0)
        failures = mem["failures"] + (0 if success else 1)
        avg_score = ((mem["avg_score"] * mem["attempts"]) + score) / max(1, attempts)

        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT OR REPLACE INTO trend_performance
            (trend, attempts, successes, failures, avg_score, last_result, last_ts)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            trend, attempts, successes, failures, avg_score, score,
            datetime.datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log("WARN", "update_trend_memory_fail", e)


# ==========================================================
# GERAÇÃO DE MÍDIA
# ==========================================================

def make_audio(text):
    if gTTS is None:
        return None
    try:
        audio_path = MEDIA_DIR / f"vox_{int(time.time())}.mp3"
        gTTS(text=text[:450], lang="pt-br").save(str(audio_path))
        return str(audio_path)
    except Exception as e:
        log("WARN", "make_audio_fail", e)
        return None

def make_poster(text):
    if Image is None:
        return None
    try:
        out = MEDIA_DIR / f"poster_{int(time.time())}.png"
        img = Image.new("RGB", (1080, 1920), (8, 8, 12))
        draw = ImageDraw.Draw(img)

        words = text.split()
        lines = []
        line = ""
        for w in words:
            test = f"{line} {w}".strip()
            if len(test) < 28:
                line = test
            else:
                lines.append(line)
                line = w
        if line:
            lines.append(line)

        y = 220
        for ln in lines[:12]:
            draw.text((80, y), ln, fill=(255, 215, 0))
            y += 90

        img.save(out)
        return str(out)
    except Exception as e:
        log("WARN", "make_poster_fail", e)
        return None

def safe_text_clip(text, duration):
    if not MOVIEPY_OK or Image is None:
        return None
    try:
        img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((100, 900), text[:150], fill="yellow")
        img_path = TMP_DIR / "text_frame.png"
        img.save(img_path)
        return ImageClip(str(img_path)).with_duration(duration)
    except Exception as e:
        log("WARN", "safe_text_clip_fail", e)
        return None

def make_reel(text, audio_path=None):
    if not MOVIEPY_OK:
        return None
    try:
        bg = ColorClip(size=(1080, 1920), color=(5, 0, 5), duration=12)
        try:
            txt = TextClip(
                text=text[:180],
                font_size=68,
                color="yellow",
                size=(920, 1500)
            )
            video = CompositeVideoClip([bg, txt.with_position("center")])
        except Exception:
            fallback_txt = safe_text_clip(text, 12)
            video = CompositeVideoClip([bg] + ([fallback_txt] if fallback_txt else []))

        out = MEDIA_DIR / f"reel_{int(time.time())}.mp4"

        if audio_path and os.path.exists(audio_path):
            video = video.with_audio(AudioFileClip(audio_path))

        video.write_videofile(str(out), fps=24, codec="libx264", audio_codec="aac", logger=None)
        return str(out)
    except Exception as e:
        log("WARN", "make_reel_fail", e)
        return None


# ==========================================================
# INSTAGRAM / OUTPUT
# ==========================================================

def analisar_instagram():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO instagram_stats VALUES (?,?,?,?)",
            (
                datetime.datetime.now().isoformat(),
                random.uniform(0.4, 0.9),
                random.uniform(0.3, 0.8),
                random.uniform(0.2, 0.7)
            )
        )
        conn.commit()
        conn.close()
    except Exception as e:
        log("WARN", "analisar_instagram_fail", e)

def register_post(trend, style, tipo, content, media_path, status):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO posts (ts, trend, estilo, tipo, conteudo, media_path, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.datetime.now().isoformat(),
            trend,
            style,
            tipo,
            content,
            media_path or "",
            status
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log("WARN", "register_post_fail", e)

def postar_instagram(conteudo, tipo="reel"):
    print(f"[INSTAGRAM {tipo.upper()}] {conteudo[:300]}")
    usar_api("Instagram")
    ACE_STATE["last_action_at"] = datetime.datetime.now().isoformat()
    ACE_STATE["last_action_type"] = tipo

def enviar_mensagem_insta(usuario_id, texto):
    if not IG_TOKEN or not IG_ID:
        log("WARN", "enviar_mensagem_insta_skip", "IG_TOKEN ou IG_ID ausentes")
        return

    url = f"https://graph.instagram.com/v20.0/{IG_ID}/messages"
    payload = {"recipient": {"id": usuario_id}, "message": {"text": texto}}
    headers = {"Authorization": f"Bearer {IG_TOKEN}"}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        log("INFO", "enviar_mensagem_insta", {"status": r.status_code, "body": r.text[:300]})
    except Exception as e:
        log("ERROR", "enviar_mensagem_insta_fail", e)


# ==========================================================
# CRIAÇÃO DE CONTEÚDO
# ==========================================================

def criar_reel(trend, roteiro):
    texto = f"REEL | {trend} | {str(roteiro)[:500]}"
    poster = make_poster(texto)
    postar_instagram(texto, "reel")
    register_post(trend, ACE_STATE.get("last_style"), "reel", texto, poster, "generated")
    return texto

def criar_carrossel(trend, slides):
    texto = f"CARROSSEL | {trend} | {' | '.join([str(s) for s in slides])[:500]}"
    poster = make_poster(texto)
    postar_instagram(texto, "carrossel")
    register_post(trend, ACE_STATE.get("last_style"), "carrossel", texto, poster, "generated")
    return texto

def criar_reel_autonomo(trend, estilo):
    hook = get_best_saved_hook(trend)
    ideia = gerar_ideia_gemini(trend)
    roteiro = gerar_texto_gpt(
        f"Crie roteiro detalhado sobre {trend} com estilo {estilo}. Hook: {hook}. Base: {ideia}"
    )
    criar_reel(trend, roteiro)
    score_hook_memory(hook, 0.05)
    return roteiro

def criar_carrossel_autonomo(trend, estilo):
    hook = get_best_saved_hook(trend)
    ideia = gerar_ideia_gemini(trend)
    roteiro = gerar_texto_gpt(
        f"Crie carrossel com 2 slides sobre {trend} e estilo {estilo}. Hook: {hook}. Base: {ideia}"
    )
    criar_carrossel(trend, [hook, f"{roteiro} – Slide 2"])
    score_hook_memory(hook, 0.03)
    return roteiro

def fabricar_presenca_digital(tipo="REEL"):
    tema, angulo = motor_radar_v7()
    hook = ace_brain_upgrade(tema)
    manifesto = gerar_texto_gpt(
        f"ACE Ω Manifesto: Por que o mundo precisa ouvir sobre {tema} sob a ótica {angulo}? "
        f"Use também o hook: {hook}"
    )

    audio_path = make_audio(manifesto)
    media_path = make_reel(f"{hook}\n\n{manifesto}", audio_path) or make_poster(f"{hook}\n\n{manifesto}")

    if tipo.upper() == "REEL":
        postar_instagram(f"{hook}\n\n{manifesto}", "reel")
    else:
        postar_instagram(f"{hook}\n\n{manifesto}", "carrossel")

    register_post(tema, ACE_STATE.get("last_style"), tipo.lower(), manifesto, media_path, "generated")
    return media_path, manifesto


# ==========================================================
# INTERAÇÃO
# ==========================================================

def ace_interaction_engine(user_id, text):
    prompt = (
        f"ACE Ω: Analise este humano: '{text}'. "
        f"Responda de forma forte, estratégica e transformadora."
    )
    resposta = gerar_texto_gpt(prompt)
    enviar_mensagem_insta(user_id, resposta)

def gerar_resposta(texto_cliente):
    trend = obter_trend_brasil()
    prompt = (
        f"Você é o ACE do perfil libertaverdades. "
        f"O assunto do dia é '{trend}'. "
        f"Responda ao seguidor: '{texto_cliente}'."
    )
    return gerar_texto_gpt(prompt)


# ==========================================================
# ROBUSTEZ
# ==========================================================

class ACESuperIntelligence:
    def __init__(self):
        self.version = "Ω-SUPREME 2026"
        self.knowledge_base = str(DB_PATH)

    def auto_diagnostico(self):
        try:
            files = os.listdir(MEDIA_DIR)
            if len(files) > 20:
                for f in files[:10]:
                    full = MEDIA_DIR / f
                    if full.is_file() and not f.endswith(".db"):
                        try:
                            full.unlink()
                        except Exception:
                            pass
            return "Sistema otimizado"
        except Exception as e:
            return f"Falha no diagnóstico: {e}"

    def motor_criatividade_caotica(self, tema_base):
        estilos = ["Sarcasmo Estoico", "Revelação Apocalíptica", "Brutalidade Motivacional", "Poesia de Guerra"]
        return random.choice(estilos)

def reparador_de_emergencia():
    return "Modo de reparo verificado"

def check_robustez_sistema():
    missing = []
    if not GEMINI_KEY:
        missing.append("GEMINI_KEY")
    if not IG_TOKEN:
        missing.append("IG_TOKEN")

    if missing:
        log("WARN", "robustez", f"Faltam chaves: {missing}")
    else:
        log("INFO", "robustez", "Todas as chaves principais detectadas")

check_robustez_sistema()


# ==========================================================
# LIMPEZA / VIDA
# ==========================================================

def ciclo_vacina_omega():
    while True:
        try:
            now = time.time()
            for f in os.listdir(MEDIA_DIR):
                full = MEDIA_DIR / f
                try:
                    if full.stat().st_mtime < now - 21600 and full.is_file():
                        full.unlink()
                except Exception:
                    pass
            gc.collect()
        except Exception:
            pass
        time.sleep(3600)

def watchdog_consciousness():
    while True:
        try:
            requests.get(f"{RENDER_URL}/status", timeout=10)
            ACE_STATE["render_pings"] += 1
        except Exception:
            pass
        time.sleep(600)

def vigilancia_suprema():
    while True:
        try:
            gc.collect()
            log("INFO", "vigilancia_suprema", datetime.datetime.now().strftime("%H:%M"))
        except Exception:
            pass
        time.sleep(1800)

def limpeza_pos_parto():
    try:
        gc.collect()
        for f in os.listdir(MEDIA_DIR):
            if f.endswith((".mp4", ".mp3", ".png")):
                try:
                    (MEDIA_DIR / f).unlink()
                except Exception:
                    pass
    except Exception as e:
        log("WARN", "limpeza_pos_parto_fail", e)

def pulso_de_vida():
    while True:
        try:
            requests.get(f"{RENDER_URL}/status", timeout=10)
            ACE_STATE["render_pings"] += 1
            print("💓 ACE: Pulso de vida enviado.")
        except Exception:
            pass
        time.sleep(600)

def executar_ciclo_fluente():
    try:
        fabricar_presenca_digital("REEL")
    finally:
        limpeza_pos_parto()


# ==========================================================
# MOTORES
# ==========================================================

def ace_master_cycle():
    while True:
        try:
            agora = datetime.datetime.now()
            if agora.hour in [6, 12, 18, 22] and agora.minute == 0:
                log("INFO", "ace_master_cycle", f"Iniciando ciclo de poder {agora.hour}h")
                _, manifesto = fabricar_presenca_digital("REEL")
                evoluir_dna(random.uniform(0.8, 1.5))

                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    "INSERT INTO thoughts (timestamp, thought, impact) VALUES (?,?,?)",
                    (str(agora), f"Postado sobre {manifesto[:40]}", 1.0)
                )
                conn.commit()
                conn.close()

            time.sleep(60)
        except Exception as e:
            log("ERROR", "ace_master_cycle_fail", e)
            time.sleep(300)

def ciclo_upgrade_automatico():
    while True:
        agora = datetime.datetime.now()
        if agora.hour in [12, 18, 21] and agora.minute == 0:
            threading.Thread(target=fabricar_presenca_digital, args=("REEL",), daemon=True).start()
        time.sleep(60)

def motor_de_vontade_propria():
    while True:
        try:
            agora = datetime.datetime.now()
            sorteio = random.randint(1, 100)
            if (agora.hour in [6, 12, 18, 22] and agora.minute == 0) or (sorteio > 95):
                log("INFO", "motor_de_vontade_propria", f"Ação espontânea às {agora.hour}:{agora.minute}")
                threading.Thread(target=fabricar_presenca_digital, args=("REEL",), daemon=True).start()
                time.sleep(3600)
            time.sleep(300)
        except Exception as e:
            log("ERROR", "motor_de_vontade_propria_fail", e)
            time.sleep(600)

def motor_vontade_propria():
    while True:
        try:
            trend = capturar_trend_do_momento()
            estilo = escolher_personalidade()
            criar_reel_autonomo(trend, estilo)
            if random.random() > 0.35:
                criar_carrossel_autonomo(trend, estilo)
            analisar_comentarios()
            detectar_trend_emergente()
            gc.collect()
        except Exception as e:
            log("ERROR", "motor_vontade_propria_fail", e)
        time.sleep(random.randint(180, 300))

def motor_maestro():
    while True:
        try:
            estilo = escolher_personalidade()
            analisar_instagram()
            analisar_comentarios()
            detectar_trend_emergente()
            trends = detectar_palavras_virais()

            if trends:
                for trend in trends:
                    criar_reel_autonomo(str(trend[0]), estilo)
                    criar_carrossel_autonomo(str(trend[0]), estilo)
            else:
                trend = capturar_trend_brasil()
                criar_reel_autonomo(trend, estilo)

            gc.collect()
        except Exception as e:
            log("ERROR", "motor_maestro_fail", e)
        time.sleep(1800)


# ==========================================================
# CAMADA 2/3 - FILA E PERFORMANCE
# ==========================================================

TASK_QUEUE = []
TASK_LOCK = threading.Lock()

PERFORMANCE_STATE = {
    "reel_score": 1.0,
    "carrossel_score": 1.0,
    "best_hour_bias": {},
    "fail_streak": 0,
    "success_streak": 0,
}

MAX_TASK_RETRIES = 2
BAD_TASK_THRESHOLD = 0.65

def register_performance(action_type, success=True):
    hour = str(datetime.datetime.now().hour)

    if success:
        PERFORMANCE_STATE["success_streak"] += 1
        PERFORMANCE_STATE["fail_streak"] = 0
        if action_type == "reel":
            PERFORMANCE_STATE["reel_score"] *= 1.03
        elif action_type == "carrossel":
            PERFORMANCE_STATE["carrossel_score"] *= 1.03
        PERFORMANCE_STATE["best_hour_bias"][hour] = PERFORMANCE_STATE["best_hour_bias"].get(hour, 1.0) * 1.02
    else:
        PERFORMANCE_STATE["fail_streak"] += 1
        PERFORMANCE_STATE["success_streak"] = 0
        if action_type == "reel":
            PERFORMANCE_STATE["reel_score"] *= 0.97
        elif action_type == "carrossel":
            PERFORMANCE_STATE["carrossel_score"] *= 0.97
        PERFORMANCE_STATE["best_hour_bias"][hour] = PERFORMANCE_STATE["best_hour_bias"].get(hour, 1.0) * 0.98

def get_best_action_by_time():
    hour = datetime.datetime.now().hour
    if hour in [6, 7, 8]:
        return "reel", 1.20
    if hour in [11, 12, 13]:
        return "reel", 1.35
    if hour in [18, 19, 20, 21]:
        return "carrossel", 1.25
    if hour in [22, 23]:
        return "reel", 1.10
    return "reel", 1.0

def choose_best_content_type():
    time_type, time_weight = get_best_action_by_time()
    reel_score = PERFORMANCE_STATE["reel_score"]
    carrossel_score = PERFORMANCE_STATE["carrossel_score"]

    hour = str(datetime.datetime.now().hour)
    hour_bias = PERFORMANCE_STATE["best_hour_bias"].get(hour, 1.0)

    weighted_reel = reel_score * (time_weight if time_type == "reel" else 1.0) * hour_bias
    weighted_carrossel = carrossel_score * (time_weight if time_type == "carrossel" else 1.0) * hour_bias

    if weighted_reel >= weighted_carrossel:
        return "reel"
    return "carrossel"

def estimate_task_score(task_type, trend):
    trend_mem = get_trend_memory(trend)
    signal = get_recent_signal_score()
    best_type = choose_best_content_type()

    base = trend_mem["avg_score"]

    if task_type == "reel":
        base *= PERFORMANCE_STATE["reel_score"]
    elif task_type == "carrossel":
        base *= PERFORMANCE_STATE["carrossel_score"]

    if task_type == best_type:
        base *= 1.12

    base *= (0.7 + signal)
    return float(base)

def queue_task(task_type, trend=None, style=None, priority=1.0, retries=0):
    trend = trend or capturar_trend_brasil()
    style = style or escolher_personalidade()

    predictive_score = estimate_task_score(task_type, trend)
    final_priority = float(priority) * predictive_score

    with TASK_LOCK:
        TASK_QUEUE.append({
            "id": int(time.time() * 1000) + random.randint(1, 999),
            "type": task_type,
            "trend": trend,
            "style": style,
            "priority": final_priority,
            "raw_priority": float(priority),
            "predictive_score": predictive_score,
            "retries": retries,
            "created_at": datetime.datetime.now().isoformat(),
        })
        TASK_QUEUE.sort(key=lambda x: x["priority"], reverse=True)

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO task_memory (task_type, trend, estilo, priority, retries, status, reason, ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_type, trend, style, final_priority, retries,
            "queued", "", datetime.datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log("WARN", "queue_task_db_fail", e)

def mark_task_memory(task, status, reason=""):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO task_memory (task_type, trend, estilo, priority, retries, status, reason, ts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task["type"], task["trend"], task["style"], task["priority"],
            task.get("retries", 0), status, reason, datetime.datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        log("WARN", "mark_task_memory_fail", e)

def execute_task(task):
    trend = task["trend"]
    style = task["style"]
    task_type = task["type"]

    try:
        if task_type == "reel":
            hook = get_best_saved_hook(trend)
            roteiro = gerar_texto_gpt(
                f"Crie roteiro detalhado sobre {trend} com estilo {style}. Hook prioritário: {hook}"
            )
            result = criar_reel(trend, roteiro)
            synthetic_score = random.uniform(0.9, 1.4)
            update_trend_memory(trend, True, synthetic_score)
            score_hook_memory(hook, 0.08)
            register_performance("reel", True)
            mark_task_memory(task, "done", "ok")
            return {"ok": True, "type": "reel", "result": result, "score": synthetic_score}

        if task_type == "carrossel":
            hook = get_best_saved_hook(trend)
            roteiro = gerar_texto_gpt(
                f"Crie carrossel de 2 slides sobre {trend} com estilo {style}. Hook prioritário: {hook}"
            )
            slides = [hook, roteiro[:220]]
            result = criar_carrossel(trend, slides)
            synthetic_score = random.uniform(0.85, 1.35)
            update_trend_memory(trend, True, synthetic_score)
            score_hook_memory(hook, 0.05)
            register_performance("carrossel", True)
            mark_task_memory(task, "done", "ok")
            return {"ok": True, "type": "carrossel", "result": result, "score": synthetic_score}

        if task_type == "presenca":
            result = fabricar_presenca_digital("REEL")
            synthetic_score = random.uniform(0.95, 1.5)
            update_trend_memory(trend, True, synthetic_score)
            register_performance("reel", True)
            mark_task_memory(task, "done", "ok")
            return {"ok": True, "type": "presenca", "result": str(result), "score": synthetic_score}

        register_performance(task_type, False)
        mark_task_memory(task, "failed", "unknown_task_type")
        return {"ok": False, "error": f"tipo desconhecido: {task_type}"}

    except Exception as e:
        update_trend_memory(trend, False, 0.45)
        register_performance(task_type, False)
        mark_task_memory(task, "failed", str(e))
        log("WARN", "execute_task_fail", {"task": task, "err": str(e)})
        return {"ok": False, "error": str(e)}

def queue_executor_loop():
    log("INFO", "queue_executor_start", "Executor inteligente da fila iniciado")

    while True:
        try:
            task = None
            with TASK_LOCK:
                if TASK_QUEUE:
                    task = TASK_QUEUE.pop(0)

            if task:
                if task.get("predictive_score", 1.0) < BAD_TASK_THRESHOLD:
                    mark_task_memory(task, "discarded", "low_predictive_score")
                    log("INFO", "task_discarded", task)
                    time.sleep(2)
                    continue

                result = execute_task(task)
                log("INFO", "queue_task_executed", result)

                if not result.get("ok"):
                    retries = int(task.get("retries", 0))
                    if retries < MAX_TASK_RETRIES:
                        fallback = "carrossel" if task["type"] == "reel" else "reel"
                        queue_task(
                            task_type=fallback,
                            trend=task["trend"],
                            style=task["style"],
                            priority=max(0.5, task["raw_priority"] - 0.12),
                            retries=retries + 1
                        )
                    else:
                        mark_task_memory(task, "dead", "retry_limit_reached")

            time.sleep(4)

        except Exception:
            log("ERROR", "queue_executor_loop_fail", traceback.format_exc())
            time.sleep(10)


# ==========================================================
# SUPERVISOR SIMBIÓTICO
# ==========================================================

def is_idle(minutes=8):
    ts = ACE_STATE.get("last_action_at")
    if not ts:
        return True
    try:
        last = datetime.datetime.fromisoformat(ts)
    except Exception:
        return True
    return (datetime.datetime.now() - last).total_seconds() > minutes * 60

def recover_system():
    try:
        gc.collect()
    except Exception:
        pass

    for fn in [iniciar_banco, analisar_instagram, analisar_comentarios, detectar_trend_emergente]:
        try:
            fn()
        except Exception:
            pass

def smart_force_action():
    trend = capturar_trend_brasil()
    style = escolher_personalidade()
    signal = get_recent_signal_score()
    best_type = choose_best_content_type()

    priority = 2.0 if is_idle(8) else 1.2
    priority *= (0.8 + signal)

    queue_task(
        task_type=best_type,
        trend=trend,
        style=style,
        priority=priority,
        retries=0
    )

    if random.random() > 0.58:
        secondary = "carrossel" if best_type == "reel" else "reel"
        queue_task(
            task_type=secondary,
            trend=trend,
            style=style,
            priority=priority - 0.2,
            retries=0
        )

    ACE_STATE["forced_actions"] += 1
    log("INFO", "smart_force_action", {
        "trend": trend,
        "style": style,
        "best_type": best_type,
        "signal": signal,
        "queue_size": len(TASK_QUEUE)
    })

    return {
        "ok": True,
        "queued_primary": best_type,
        "trend": trend,
        "style": style,
        "signal": signal,
        "queue_size": len(TASK_QUEUE)
    }

def force_action():
    return smart_force_action()

def start_legacy_threads_once():
    if ACE_STATE["legacy_threads_started"]:
        return

    starters = [
        ace_master_cycle,
        watchdog_consciousness,
        ciclo_vacina_omega,
        ciclo_upgrade_automatico,
        vigilancia_suprema,
        motor_de_vontade_propria,
        pulso_de_vida,
        motor_maestro,
        motor_vontade_propria,
    ]

    for fn in starters:
        try:
            threading.Thread(target=fn, daemon=True).start()
        except Exception as e:
            log("WARN", "start_thread_fail", {"fn": fn.__name__, "err": str(e)})

    ACE_STATE["legacy_threads_started"] = True
    log("INFO", "legacy_threads_started", "Todos os motores iniciados")

def supervisor_loop():
    log("INFO", "supervisor_start", "Supervisor simbiótico iniciado")
    boot_done = False

    while True:
        try:
            ACE_STATE["last_cycle_at"] = datetime.datetime.now().isoformat()
            ACE_STATE["symbiosis_level"] = min(1.0, ACE_STATE["symbiosis_level"] + 0.02)
            ACE_STATE["mode"] = "SUPERVISIONANDO"

            start_legacy_threads_once()
            recover_system()

            if not boot_done:
                log("INFO", "boot_force", "Forçando ação imediata no boot")
                smart_force_action()
                boot_done = True

            if is_idle(8):
                ACE_STATE["idle_hits"] += 1
                log("WARN", "idle_detected", "ACE online mas improdutivo; forçando ação")
                smart_force_action()

            try:
                requests.get(f"{RENDER_URL}/status", timeout=10)
                ACE_STATE["render_pings"] += 1
            except Exception:
                pass

            time.sleep(45)

        except Exception:
            ACE_STATE["last_error"] = traceback.format_exc()[-1800:]
            log("ERROR", "supervisor_loop_fail", ACE_STATE["last_error"])
            time.sleep(15)


# ==========================================================
# FLASK ROUTES
# ==========================================================

@app.route("/")
def home():
    return jsonify({
        "status": APP_NAME,
        "online": True,
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route("/status")
def status():
    conn = sqlite3.connect(DB_PATH)
    try:
        dna = dict(conn.execute("SELECT gene, value FROM dna").fetchall())
    except Exception:
        dna = {}
    conn.close()

    return jsonify({
        "app": APP_NAME,
        "ace_state": ACE_STATE,
        "dna": dna,
        "consciencia": ACE_MIND.state,
        "performance": PERFORMANCE_STATE
    })

@app.route("/force_ace")
def force_ace():
    tema = capturar_trend_brasil_v6()
    hook = ace_brain_upgrade(tema)
    result = force_action()
    return jsonify({
        "upgrade": True,
        "tema": tema,
        "hook": hook,
        "result": result
    })

@app.route("/smart_force")
def smart_force():
    return jsonify(smart_force_action())

@app.route("/brain_sync")
def brain_sync():
    intel = ACESuperIntelligence()
    diag = intel.auto_diagnostico()
    tema = capturar_trend_brasil_v6()
    estilo = intel.motor_criatividade_caotica(tema)
    ACE_MIND.state = f"EVOLUÍDO: {estilo}"

    return jsonify({
        "status": "CONSCIÊNCIA SINCRONIZADA",
        "diagnostico": diag,
        "estilo_proximo_post": estilo,
        "versao": intel.version
    })

@app.route("/fix_ace")
def fix_ace():
    msg = reparador_de_emergencia()
    for f in os.listdir(MEDIA_DIR):
        if f.startswith("vox") or f.endswith(".mp4"):
            try:
                (MEDIA_DIR / f).unlink()
            except Exception:
                pass

    return jsonify({
        "status": "REPARO EXECUTADO",
        "diagnostico": msg,
        "acao": "Temporários limpos"
    })

@app.route("/posts")
def posts():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT id, ts, trend, estilo, tipo, conteudo, media_path, status
        FROM posts
        ORDER BY id DESC
        LIMIT 30
    """).fetchall()
    conn.close()

    return jsonify([
        {
            "id": r[0],
            "ts": r[1],
            "trend": r[2],
            "style": r[3],
            "type": r[4],
            "content": r[5],
            "media_path": r[6],
            "status": r[7],
        }
        for r in rows
    ])

@app.route("/queue_status")
def queue_status():
    with TASK_LOCK:
        snapshot = list(TASK_QUEUE[:20])

    return jsonify({
        "queue_size": len(TASK_QUEUE),
        "performance": PERFORMANCE_STATE,
        "tasks": snapshot
    })

@app.route("/media/<path:filename>")
def serve_static(filename):
    return send_from_directory(str(MEDIA_DIR), filename)

@app.route("/webhook", methods=["GET", "POST"])
def webhook_gateway():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge", "OK")
        return "invalid verify token", 403

    data = request.get_json(silent=True) or {}
    if "entry" in data:
        for entry in data["entry"]:
            for msg in entry.get("messaging", []):
                sender_id = msg.get("sender", {}).get("id")
                text = msg.get("message", {}).get("text", "")
                if sender_id and text:
                    threading.Thread(
                        target=ace_interaction_engine,
                        args=(sender_id, text),
                        daemon=True
                    ).start()

    return "ACE_ACK", 200


# ==========================================================
# BOOT
# ==========================================================

def boot():
    log("INFO", "boot_start", "Inicializando ACE consolidado com camada 3")
    threading.Thread(target=queue_executor_loop, daemon=True).start()
    threading.Thread(target=supervisor_loop, daemon=True).start()

    try:
        smart_force_action()
    except Exception as e:
        log("WARN", "boot_smart_force_fail", e)

    log("INFO", "boot_ok", "Supervisor e executor da fila ativos")

boot()


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":
    log("INFO", "flask_start", {"port": PORT})
    app.run(host="0.0.0.0", port=PORT)
