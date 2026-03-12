# ==========================================================
# ACE Ω SUPREME - CONSOLIDADO FINAL COM CAMADA 4 + TOKEN CALLBACK
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
import hashlib
import unicodedata
from pathlib import Path
from difflib import SequenceMatcher
from urllib.parse import urlencode

import requests
import numpy as np
from flask import Flask, jsonify, request, send_from_directory, redirect

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

def ace_env(key, default=None):
    return os.environ.get(key, default)

APP_NAME = "ACE Ω SUPREME"
PORT = int(ace_env("PORT", "10000"))
VERIFY_TOKEN = ace_env("VERIFY_TOKEN", "ACE_SIGILO_2026")

RENDER_URL = ace_env(
    "RENDER_EXTERNAL_URL",
    f"https://{ace_env('RENDER_EXTERNAL_HOSTNAME', 'localhost')}"
)

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
AUTH_PATH = MEMORY_DIR / "instagram_auth.json"

# --- Chaves ---
IG_TOKEN_ENV = ace_env("IG_TOKEN")
IG_ID_ENV = ace_env("IG_ID")
GEMINI_KEY = ace_env("GEMINI_KEY")
OPENAI_API_KEY = ace_env("OPENAI_API_KEY")

# App ID / Secret do app Meta / Instagram Login
INSTAGRAM_APP_ID = (
    ace_env("INSTAGRAM_APP_ID")
    or ace_env("FACEBOOK_APP_ID")
    or ace_env("APP_ID")
    or ""
)

INSTAGRAM_APP_SECRET = (
    ace_env("INSTAGRAM_APP_SECRET")
    or ace_env("FACEBOOK_APP_SECRET")
    or ace_env("APP_SECRET")
    or ""
)

# runtime auth
IG_TOKEN_RUNTIME = None
IG_ID_RUNTIME = None

# callback do login Instagram
INSTAGRAM_REDIRECT_URI = ace_env("INSTAGRAM_REDIRECT_URI", f"{RENDER_URL}/instagram/token")

app = Flask(__name__)

GEMINI_MODEL = None
GEMINI_MODEL_NAMES = [
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-002",
    "gemini-1.5-flash",
]

if genai and GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        for model_name in GEMINI_MODEL_NAMES:
            try:
                GEMINI_MODEL = genai.GenerativeModel(model_name)
                break
            except Exception:
                continue
    except Exception:
        GEMINI_MODEL = None


# ==========================================================
# AUTH RUNTIME
# ==========================================================

def get_ig_token():
    return IG_TOKEN_RUNTIME or IG_TOKEN_ENV

def get_ig_id():
    return IG_ID_RUNTIME or IG_ID_ENV

def save_instagram_auth(token=None, user_id=None, meta=None):
    global IG_TOKEN_RUNTIME, IG_ID_RUNTIME
    payload = {
        "token": token or get_ig_token(),
        "user_id": user_id or get_ig_id(),
        "saved_at": datetime.datetime.now().isoformat(),
        "meta": meta or {},
    }
    try:
        AUTH_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

    if payload.get("token"):
        IG_TOKEN_RUNTIME = payload["token"]
    if payload.get("user_id"):
        IG_ID_RUNTIME = str(payload["user_id"])

def load_instagram_auth():
    global IG_TOKEN_RUNTIME, IG_ID_RUNTIME
    if not AUTH_PATH.exists():
        return
    try:
        data = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
        IG_TOKEN_RUNTIME = data.get("token") or IG_TOKEN_RUNTIME
        IG_ID_RUNTIME = str(data.get("user_id")) if data.get("user_id") else IG_ID_RUNTIME
    except Exception:
        pass

load_instagram_auth()


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
    "instagram_connected": bool(get_ig_token() and get_ig_id()),
    "instagram_last_auth_at": None,
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

    # ===== CAMADA 4 =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ace_trend_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trend TEXT NOT NULL,
            trend_norm TEXT NOT NULL,
            used_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ace_trend_history_norm_used_at
        ON ace_trend_history(trend_norm, used_at)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ace_content_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            trend TEXT,
            trend_norm TEXT,
            content_type TEXT,
            title TEXT,
            hook TEXT,
            body TEXT,
            content_hash TEXT,
            score REAL DEFAULT 0,
            status TEXT DEFAULT 'generated',
            reason TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ace_content_history_created_at
        ON ace_content_history(created_at)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ace_candidate_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            trend TEXT,
            trend_norm TEXT,
            content_type TEXT,
            title TEXT,
            hook TEXT,
            body TEXT,
            meta_json TEXT,
            score REAL DEFAULT 0,
            selected INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS instagram_auth_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT,
            action TEXT,
            detail TEXT
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
        for model_name in GEMINI_MODEL_NAMES:
            try:
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(
                    f"Crie uma ideia curta, forte e clara em português do Brasil sobre: {trend}"
                )
                text = getattr(resp, "text", None)
                if text:
                    return text.strip()
            except Exception as e:
                log("WARN", f"gerar_ideia_gemini_fail_{model_name}", e)

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
# CAMADA 4 - GOVERNANÇA
# ==========================================================

ACE_LAYER4_CONFIG = {
    "cooldown_minutes": int(ace_env("ACE_COOLDOWN_MINUTES", "60")),
    "max_posts_per_hour": int(ace_env("ACE_MAX_POSTS_PER_HOUR", "4")),
    "min_trend_chars": int(ace_env("ACE_MIN_TREND_CHARS", "4")),
    "min_trend_words": int(ace_env("ACE_MIN_TREND_WORDS", "2")),
    "similarity_threshold": float(ace_env("ACE_SIMILARITY_THRESHOLD", "0.80")),
    "history_compare_limit": int(ace_env("ACE_HISTORY_COMPARE_LIMIT", "50")),
}

ACE_LAYER4_LOCK = threading.Lock()

ACE_STOPWORDS = {
    "a", "o", "e", "é", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "um", "uma", "uns", "umas", "por", "para", "com", "sem",
    "sobre", "até", "que", "se", "eu", "tu", "ele", "ela", "nós", "vos",
    "eles", "elas", "isso", "isto", "aquilo", "me", "te", "lhe", "lhes",
    "já", "vai", "foi", "ser", "ter", "tem", "há", "aqui", "ali", "lá",
    "como", "mais", "menos", "muito", "muita", "muitos", "muitas",
    "ninguem", "ninguém", "explica", "acontecendo", "mudou", "mudança",
    "coisa", "coisas", "hoje", "ontem", "amanha", "amanhã", "agora",
    "tipo", "assim", "aquele", "essa"
}

def ace_strip_accents(text):
    if not text:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    )

def ace_normalize_text(text):
    text = (text or "").strip().lower()
    text = ace_strip_accents(text)
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[@#]\w+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def ace_tokenize(text):
    norm = ace_normalize_text(text)
    return [t for t in norm.split() if t]

def ace_compact_signature(text):
    norm = ace_normalize_text(text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

def ace_jaccard_similarity(a, b):
    ta = set(ace_tokenize(a))
    tb = set(ace_tokenize(b))
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta | tb))

def ace_sequence_similarity(a, b):
    return SequenceMatcher(None, ace_normalize_text(a), ace_normalize_text(b)).ratio()

def ace_combined_similarity(a, b):
    seq = ace_sequence_similarity(a, b)
    jac = ace_jaccard_similarity(a, b)
    return (seq * 0.6) + (jac * 0.4)

def ace_is_bad_trend(trend):
    raw = (trend or "").strip()
    norm = ace_normalize_text(raw)
    words = ace_tokenize(raw)

    if not raw:
        return True, "trend_vazia"
    if len(norm) < ACE_LAYER4_CONFIG["min_trend_chars"]:
        return True, "trend_curta"
    if len(words) < ACE_LAYER4_CONFIG["min_trend_words"]:
        return True, "trend_sem_contexto"

    meaningful = [w for w in words if w not in ACE_STOPWORDS and len(w) >= 3]
    if len(meaningful) < 2:
        return True, "trend_fraca_sem_semantica"

    if len(set(words)) == 1:
        return True, "trend_repetitiva"

    bad_patterns = [
        r"^(ninguem|ninguem aceita|explica|acontecendo|mudou)$",
        r"^(viral|trend|assunto|tema)$",
    ]
    for pattern in bad_patterns:
        if re.match(pattern, norm):
            return True, "trend_generica"

    return False, "ok"

def ace_register_trend_usage(trend):
    now = datetime.datetime.now().isoformat()
    trend_norm = ace_normalize_text(trend)
    with ACE_LAYER4_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO ace_trend_history (trend, trend_norm, used_at)
            VALUES (?, ?, ?)
        """, (trend, trend_norm, now))
        conn.commit()
        conn.close()

def ace_trend_in_cooldown(trend):
    trend_norm = ace_normalize_text(trend)
    limit_time = (
        datetime.datetime.now() -
        datetime.timedelta(minutes=ACE_LAYER4_CONFIG["cooldown_minutes"])
    ).isoformat()

    with ACE_LAYER4_LOCK:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("""
            SELECT used_at FROM ace_trend_history
            WHERE trend_norm = ? AND used_at >= ?
            ORDER BY used_at DESC
            LIMIT 1
        """, (trend_norm, limit_time)).fetchone()
        conn.close()

    if row:
        return True, f"cooldown_ativo_ate_{row[0]}"
    return False, "ok"

def ace_count_recent_posts(hours=1):
    limit_time = (datetime.datetime.now() - datetime.timedelta(hours=hours)).isoformat()
    with ACE_LAYER4_LOCK:
        conn = sqlite3.connect(DB_PATH)
        row = conn.execute("""
            SELECT COUNT(*) FROM ace_content_history
            WHERE created_at >= ?
            AND status IN ('approved', 'published', 'generated')
        """, (limit_time,)).fetchone()
        conn.close()
    return int(row[0]) if row else 0

def ace_rate_limit_blocked():
    recent = ace_count_recent_posts(hours=1)
    if recent >= ACE_LAYER4_CONFIG["max_posts_per_hour"]:
        return True, f"limite_hora_atingido_{recent}"
    return False, "ok"

def ace_recent_history(limit=None):
    limit = limit or ACE_LAYER4_CONFIG["history_compare_limit"]
    with ACE_LAYER4_LOCK:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute(f"""
            SELECT id, created_at, trend, content_type, title, hook, body, content_hash, score, status
            FROM ace_content_history
            ORDER BY id DESC
            LIMIT {int(limit)}
        """).fetchall()
        conn.close()
    return rows

def ace_is_duplicate_content(title, hook, body):
    candidate_text = " ".join([title or "", hook or "", body or ""]).strip()
    if not candidate_text:
        return True, "conteudo_vazio", None

    candidate_hash = ace_compact_signature(candidate_text)
    rows = ace_recent_history()

    threshold = ACE_LAYER4_CONFIG["similarity_threshold"]
    best_match = None
    best_score = 0.0

    for row in rows:
        existing_text = " ".join([
            row[4] or "",
            row[5] or "",
            row[6] or ""
        ]).strip()

        if row[7] == candidate_hash:
            return True, "hash_igual", {
                "history_id": row[0],
                "similarity": 1.0,
                "title": row[4]
            }

        sim = ace_combined_similarity(candidate_text, existing_text)
        if sim > best_score:
            best_score = sim
            best_match = row

        if sim >= threshold:
            return True, "similaridade_alta", {
                "history_id": row[0],
                "similarity": round(sim, 4),
                "title": row[4]
            }

    return False, "ok", {
        "best_similarity": round(best_score, 4),
        "best_history_id": best_match[0] if best_match else None
    }

def ace_emotional_intensity(text):
    norm = ace_normalize_text(text)
    strong_words = {
        "verdade", "erro", "crise", "medo", "ansiedade", "proposito",
        "propósito", "disciplina", "fracasso", "segredo", "pare",
        "urgente", "alerta", "liberdade", "mudanca", "mudança",
        "destrava", "mentalidade", "fe", "fé", "deus", "jesus", "davi"
    }
    tokens = set(norm.split())
    hits = len(tokens & strong_words)
    return min(1.0, hits / 5.0)

def ace_curiosity_gap(title, hook):
    text = f"{title or ''} {hook or ''}".lower()
    patterns = [
        "ninguém", "ninguem", "verdade", "segredo", "por que",
        "porque", "o que", "como", "erro", "motivo", "prova", "sinal"
    ]
    hits = sum(1 for p in patterns if p in text)
    return min(1.0, hits / 4.0)

def ace_novelty_score(title, hook, body):
    duplicated, _, info = ace_is_duplicate_content(title, hook, body)
    if duplicated:
        return 0.0
    best_similarity = (info or {}).get("best_similarity", 0.0)
    novelty = 1.0 - float(best_similarity)
    return max(0.0, min(1.0, novelty))

def ace_trend_strength(trend):
    bad, _ = ace_is_bad_trend(trend)
    if bad:
        return 0.0
    words = ace_tokenize(trend)
    meaningful = [w for w in words if w not in ACE_STOPWORDS and len(w) >= 3]
    base = min(1.0, len(meaningful) / 4.0)
    return max(0.0, min(1.0, base))

def ace_calculate_post_score(trend, title, hook, body):
    ts = ace_trend_strength(trend)
    nv = ace_novelty_score(title, hook, body)
    ei = ace_emotional_intensity(" ".join([trend or "", title or "", hook or ""]))
    cg = ace_curiosity_gap(title, hook)

    score = (
        ts * 0.30 +
        nv * 0.30 +
        ei * 0.20 +
        cg * 0.20
    )
    return round(max(0.0, min(1.0, score)), 4)

def ace_register_content_history(trend, content_type, title, hook, body, score, status="approved", reason=""):
    now = datetime.datetime.now().isoformat()
    trend_norm = ace_normalize_text(trend)
    content_hash = ace_compact_signature(" ".join([title or "", hook or "", body or ""]))

    with ACE_LAYER4_LOCK:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            INSERT INTO ace_content_history
            (created_at, trend, trend_norm, content_type, title, hook, body, content_hash, score, status, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            now, trend, trend_norm, content_type, title, hook, body,
            content_hash, float(score), status, reason
        ))
        conn.commit()
        conn.close()

def ace_govern_post(trend, content_type, title, hook, body):
    bad_trend, trend_reason = ace_is_bad_trend(trend)
    if bad_trend:
        ace_register_content_history(trend, content_type, title, hook, body, 0.0, "blocked", f"trend:{trend_reason}")
        return {
            "approved": False,
            "reason": f"trend_bloqueada:{trend_reason}",
            "score": 0.0
        }

    cooldown, cooldown_reason = ace_trend_in_cooldown(trend)
    if cooldown:
        ace_register_content_history(trend, content_type, title, hook, body, 0.0, "blocked", f"cooldown:{cooldown_reason}")
        return {
            "approved": False,
            "reason": f"cooldown:{cooldown_reason}",
            "score": 0.0
        }

    limited, limit_reason = ace_rate_limit_blocked()
    if limited:
        ace_register_content_history(trend, content_type, title, hook, body, 0.0, "blocked", f"rate:{limit_reason}")
        return {
            "approved": False,
            "reason": f"rate_limit:{limit_reason}",
            "score": 0.0
        }

    duplicate, duplicate_reason, duplicate_info = ace_is_duplicate_content(title, hook, body)
    if duplicate:
        ace_register_content_history(trend, content_type, title, hook, body, 0.0, "blocked", f"duplicate:{duplicate_reason}")
        return {
            "approved": False,
            "reason": f"duplicado:{duplicate_reason}",
            "score": 0.0,
            "data": duplicate_info
        }

    score = ace_calculate_post_score(trend, title, hook, body)
    ace_register_content_history(trend, content_type, title, hook, body, score, "approved", "ok")
    ace_register_trend_usage(trend)

    return {
        "approved": True,
        "reason": "ok",
        "score": score
    }


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
    token = get_ig_token()
    ig_id = get_ig_id()

    if not token or not ig_id:
        log("WARN", "enviar_mensagem_insta_skip", "IG_TOKEN ou IG_ID ausentes")
        return

    url = f"https://graph.instagram.com/v20.0/{ig_id}/messages"
    payload = {"recipient": {"id": usuario_id}, "message": {"text": texto}}
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        log("INFO", "enviar_mensagem_insta", {"status": r.status_code, "body": r.text[:300]})
    except Exception as e:
        log("ERROR", "enviar_mensagem_insta_fail", e)


# ==========================================================
# HELPER ÚNICO DE PUBLICAÇÃO GOVERNADA
# ==========================================================

def processar_publicacao_governada(trend, estilo, tipo, title, hook, body, media_path=None):
    govern = ace_govern_post(
        trend=trend,
        content_type=tipo,
        title=title,
        hook=hook,
        body=body
    )

    if not govern["approved"]:
        log("INFO", "post_blocked_layer4", govern)
        register_post(trend, estilo, tipo, body, media_path, f"blocked:{govern['reason']}")
        return {
            "ok": False,
            "blocked": True,
            "reason": govern["reason"],
            "score": govern.get("score", 0.0),
            "content": body,
            "media_path": media_path
        }

    postar_instagram(body, tipo)
    register_post(trend, estilo, tipo, body, media_path, "generated")

    return {
        "ok": True,
        "blocked": False,
        "reason": "ok",
        "score": govern["score"],
        "content": body,
        "media_path": media_path
    }


# ==========================================================
# CRIAÇÃO DE CONTEÚDO
# ==========================================================

def criar_reel(trend, roteiro):
    hook = get_best_saved_hook(trend)
    texto = f"REEL | {trend} | {str(roteiro)[:500]}"
    poster = make_poster(texto)
    return processar_publicacao_governada(
        trend=trend,
        estilo=ACE_STATE.get("last_style"),
        tipo="reel",
        title=hook,
        hook=hook,
        body=texto,
        media_path=poster
    )

def criar_carrossel(trend, slides):
    hook = get_best_saved_hook(trend)
    texto = f"CARROSSEL | {trend} | {' | '.join([str(s) for s in slides])[:500]}"
    poster = make_poster(texto)
    return processar_publicacao_governada(
        trend=trend,
        estilo=ACE_STATE.get("last_style"),
        tipo="carrossel",
        title=hook,
        hook=hook,
        body=texto,
        media_path=poster
    )

def criar_reel_autonomo(trend, estilo):
    hook = get_best_saved_hook(trend)
    ideia = gerar_ideia_gemini(trend)
    roteiro = gerar_texto_gpt(
        f"Crie roteiro detalhado sobre {trend} com estilo {estilo}. Hook: {hook}. Base: {ideia}"
    )
    result = criar_reel(trend, roteiro)
    if result.get("ok"):
        score_hook_memory(hook, 0.05)
    return result

def criar_carrossel_autonomo(trend, estilo):
    hook = get_best_saved_hook(trend)
    ideia = gerar_ideia_gemini(trend)
    roteiro = gerar_texto_gpt(
        f"Crie carrossel com 2 slides sobre {trend} e estilo {estilo}. Hook: {hook}. Base: {ideia}"
    )
    result = criar_carrossel(trend, [hook, f"{roteiro} – Slide 2"])
    if result.get("ok"):
        score_hook_memory(hook, 0.03)
    return result

def fabricar_presenca_digital(tipo="REEL"):
    tema, angulo = motor_radar_v7()
    hook = ace_brain_upgrade(tema)
    manifesto = gerar_texto_gpt(
        f"ACE Ω Manifesto: Por que o mundo precisa ouvir sobre {tema} sob a ótica {angulo}? "
        f"Use também o hook: {hook}"
    )

    audio_path = make_audio(manifesto)
    media_path = make_reel(f"{hook}\n\n{manifesto}", audio_path) or make_poster(f"{hook}\n\n{manifesto}")

    body = f"{hook}\n\n{manifesto}"
    tipo_norm = "reel" if tipo.upper() == "REEL" else "carrossel"

    result = processar_publicacao_governada(
        trend=tema,
        estilo=ACE_STATE.get("last_style"),
        tipo=tipo_norm,
        title=hook,
        hook=hook,
        body=body,
        media_path=media_path
    )

    return media_path, manifesto, result


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
    if not get_ig_token():
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
                _, manifesto, pub = fabricar_presenca_digital("REEL")
                evoluir_dna(random.uniform(0.8, 1.5))

                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    "INSERT INTO thoughts (timestamp, thought, impact) VALUES (?,?,?)",
                    (str(agora), f"Postado sobre {manifesto[:40]}", 1.0 if pub.get('ok') else 0.4)
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

            if result.get("ok"):
                synthetic_score = random.uniform(0.9, 1.4)
                update_trend_memory(trend, True, synthetic_score)
                score_hook_memory(hook, 0.08)
                register_performance("reel", True)
                mark_task_memory(task, "done", "ok")
                return {"ok": True, "type": "reel", "result": result, "score": synthetic_score}

            update_trend_memory(trend, False, 0.45)
            register_performance("reel", False)
            mark_task_memory(task, "blocked", result.get("reason", "blocked"))
            return {"ok": False, "type": "reel", "error": result.get("reason", "blocked")}

        if task_type == "carrossel":
            hook = get_best_saved_hook(trend)
            roteiro = gerar_texto_gpt(
                f"Crie carrossel de 2 slides sobre {trend} com estilo {style}. Hook prioritário: {hook}"
            )
            slides = [hook, roteiro[:220]]
            result = criar_carrossel(trend, slides)

            if result.get("ok"):
                synthetic_score = random.uniform(0.85, 1.35)
                update_trend_memory(trend, True, synthetic_score)
                score_hook_memory(hook, 0.05)
                register_performance("carrossel", True)
                mark_task_memory(task, "done", "ok")
                return {"ok": True, "type": "carrossel", "result": result, "score": synthetic_score}

            update_trend_memory(trend, False, 0.45)
            register_performance("carrossel", False)
            mark_task_memory(task, "blocked", result.get("reason", "blocked"))
            return {"ok": False, "type": "carrossel", "error": result.get("reason", "blocked")}

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
            ACE_STATE["instagram_connected"] = bool(get_ig_token() and get_ig_id())

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
# INSTAGRAM OAUTH / TOKEN CALLBACK
# ==========================================================

def log_auth(action, detail):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            "INSERT INTO instagram_auth_log (ts, action, detail) VALUES (?, ?, ?)",
            (datetime.datetime.now().isoformat(), action, str(detail)[:4000])
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def build_instagram_oauth_url(mode="basic"):
    if not INSTAGRAM_APP_ID:
        return None

    if mode == "basic":
        scope_list = [
            "instagram_business_basic"
        ]
    else:
        scope_list = [
            "instagram_business_basic",
            "instagram_business_content_publish",
            "instagram_business_manage_comments",
            "instagram_business_manage_messages",
            "instagram_business_manage_insights",
        ]

    params = {
        "client_id": INSTAGRAM_APP_ID,
        "redirect_uri": INSTAGRAM_REDIRECT_URI,
        "response_type": "code",
        "scope": ",".join(scope_list)
    }
    return f"https://www.instagram.com/oauth/authorize?{urlencode(params)}"

def exchange_code_for_token(code):
    
    if not INSTAGRAM_APP_ID or not INSTAGRAM_APP_SECRET:
        return {
            "ok": False,
            "error": "INSTAGRAM_APP_ID ou INSTAGRAM_APP_SECRET ausentes"
        }

    url = "https://api.instagram.com/oauth/access_token"
    data = {
        "client_id": INSTAGRAM_APP_ID,
        "client_secret": INSTAGRAM_APP_SECRET,
        "grant_type": "authorization_code",
        "redirect_uri": INSTAGRAM_REDIRECT_URI,
        "code": code,
    }

    try:
        r = requests.post(url, data=data, timeout=30)
        body = {}
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text[:1000]}

        log_auth("exchange_code", {"status": r.status_code, "body": body})

        if r.status_code >= 400:
            return {
                "ok": False,
                "status": r.status_code,
                "error": body
            }

        access_token = body.get("access_token")
        user_id = body.get("user_id")

        if access_token:
            save_instagram_auth(
                token=access_token,
                user_id=user_id,
                meta={"source": "callback_code_exchange"}
            )
            ACE_STATE["instagram_connected"] = bool(get_ig_token() and get_ig_id())
            ACE_STATE["instagram_last_auth_at"] = datetime.datetime.now().isoformat()

        return {
            "ok": True,
            "data": body
        }

    except Exception as e:
        log_auth("exchange_code_fail", str(e))
        return {
            "ok": False,
            "error": str(e)
        }


# ==========================================================
# FLASK ROUTES
# ==========================================================

@app.route("/")
def home():
    return jsonify({
        "status": APP_NAME,
        "online": True,
        "timestamp": datetime.datetime.now().isoformat(),
        "instagram_connected": bool(get_ig_token() and get_ig_id())
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
        "performance": PERFORMANCE_STATE,
        "instagram": {
            "connected": bool(get_ig_token() and get_ig_id()),
            "ig_id": get_ig_id(),
            "token_present": bool(get_ig_token()),
            "redirect_uri": INSTAGRAM_REDIRECT_URI,
        }
    })

@app.route("/state")
def state_alias():
    return status()

@app.route("/force")
def force_alias():
    return jsonify(force_action())

@app.route("/tasks")
def tasks_alias():
    return queue_status()

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


@app.route("/instagram/auth")
def instagram_auth():
@app.route("/instagram/token", methods=["GET"])
def instagram_token_callback():
    code = request.args.get("code", "").strip()
    error = request.args.get("error")
    error_reason = request.args.get("error_reason")
    error_description = request.args.get("error_description")

    if error:
        return jsonify({
            "ok": False,
            "stage": "instagram_auth",
            "error": error,
            "error_reason": error_reason,
            "error_description": error_description
        }), 400

    if not code:
        return jsonify({
            "ok": True,
            "message": "Endpoint ativo. Use /instagram/auth para iniciar o login.",
            "redirect_uri_correto": INSTAGRAM_REDIRECT_URI,
            "token_present": bool(get_ig_token()),
            "ig_id": get_ig_id()
        }), 200

    result = exchange_code_for_token(code)

    if result.get("ok"):
        return jsonify({
            "ok": True,
            "message": "Token capturado com sucesso",
            "user_id": get_ig_id(),
            "token_present": bool(get_ig_token()),
            "coloque_no_render": {
                "IG_TOKEN": get_ig_token(),
                "IG_ID": get_ig_id()
            }
        }), 200

    return jsonify({
        "ok": False,
        "message": "Falha ao trocar code por token",
        "error": result.get("error")
    }), 400

@app.route("/media/<path:filename>")
def serve_static(filename):
    return send_from_directory(str(MEDIA_DIR), filename)

@app.route("/webhook", methods=["GET", "POST"])
def webhook_gateway():
    # 1) verificação de webhook Meta
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge", "OK")
        return "invalid verify token", 403

    # 2) eventos webhook
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
    log("INFO", "boot_start", "Inicializando ACE consolidado com camada 4")
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
