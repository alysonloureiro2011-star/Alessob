

# ==========================================================
# 🚀 ACE Ω V6000+ AUTOMÁTICO — CRONIFICADO & ONE-CLICK
# ==========================================================

import os, time, datetime, threading, random, re, json, sqlite3, math
import requests
import numpy as np
from collections import Counter
from google import genai
from pytrends.request import TrendReq
from flask import Flask, send_from_directory, request
from pyngrok import ngrok
from moviepy.editor import ColorClip, TextClip, CompositeVideoClip, AudioFileClip, vfx
from PIL import Image, ImageDraw
from gtts import gTTS

# ==========================================================
# 🔐 VARIÁVEIS DE AMBIENTE
# ==========================================================

def safe_get_env(key, default="DEMO"):
    return os.environ.get(key, default)

IG_TOKEN = safe_get_env("IG_TOKEN")
GEMINI_KEY = safe_get_env("GEMINI_KEY")
IG_ID = safe_get_env("IG_ID")
NGROK_TOKEN = safe_get_env("NGROK_TOKEN")
VERIFY_TOKEN = "ACE_SIGILO_2026"

client = genai.Client(api_key=GEMINI_KEY)
app = Flask(__name__)
OUT_PATH = "/content/ace_media/" if os.path.exists("/content/") else "./ace_media/"
os.makedirs(OUT_PATH, exist_ok=True)

# ==========================================================
# 🧠 MEMÓRIA EVOLUTIVA
# ==========================================================

DB_PATH = OUT_PATH + "ace_memory.db"

def init_memory():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS posts(
        id INTEGER PRIMARY KEY,
        data TEXT,
        tema TEXT,
        hook TEXT,
        score REAL
    )
    """)
    conn.commit()
    conn.close()

init_memory()

# ==========================================================
# 🌍 RADAR GLOBAL
# ==========================================================

def radar_global():
    termos=[]
    try:
        pytrend = TrendReq(hl='pt-BR')
        trending = pytrend.trending_searches(pn='brazil')
        termos += list(trending[0])
    except: pass
    palavras=[]
    for t in termos:
        palavras += re.findall(r'\w+', t.lower())
    freq = Counter(palavras)
    if not freq: return "disciplina"
    return freq.most_common(1)[0][0]

# ==========================================================
# ⚡ MOTOR DE DOPAMINA
# ==========================================================

gatilhos=["segredo","verdade","erro","oculto","alerta","proibido"]

def score_dopamina(texto):
    score=1.0
    for g in gatilhos:
        if g in texto.lower(): score*=1.25
    if "?" in texto: score*=1.1
    return score

# ==========================================================
# 🧠 GERADOR DE HOOKS
# ==========================================================

def gerar_hook(tema):
    hooks=[
        f"A verdade que ninguém aceita sobre {tema}",
        f"O erro silencioso em {tema}",
        f"O segredo oculto de {tema}",
        f"O alerta brutal sobre {tema}"
    ]
    return max(hooks,key=score_dopamina)

# ==========================================================
# 🧬 GENES
# ==========================================================

GENES={"zoom":0.05,"contraste":1.1,"caos":0.2}

def mutacao(score):
    if score>1.2:
        GENES["zoom"]*=1.05
        GENES["contraste"]*=1.02
    else:
        GENES["zoom"]*=0.97
        GENES["contraste"]*=0.99

# ==========================================================
# 🧠 MEMÓRIA
# ==========================================================

def registrar_post(tema,hook,score):
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("INSERT INTO posts(data,tema,hook,score) VALUES(?,?,?,?)",
              (str(datetime.datetime.now()),tema,hook,score))
    conn.commit()
    conn.close()

# ==========================================================
# 🧠 MOTOR OMNI V4000
# ==========================================================

def motor_omni_v4000(entrada):
    try: trend=TrendReq(hl='pt-BR').trending_searches(pn='brazil')[0][0]
    except: trend="Dominação Digital"
    instrucao=f"ACE libertaverdades. Trend: {trend}. Brutalidade estoica."
    res = client.models.generate_content(model="gemini-2.0-flash",contents=f"{instrucao}\n\n{entrada}")
    return res.text

# ==========================================================
# 🎨 STUDIO V4000
# ==========================================================

def fabricar_arsenal_v4000():
    print("🎨 STUDIO V4000 ATIVO")
    texto = motor_omni_v4000("Gere 10 verdades.")
    frases = re.split(r'\d\.', texto)[1:11]
    audio_p = OUT_PATH + "voice.mp3"
    gTTS(text=texto[:400],lang='pt-br').save(audio_p)
    bg = ColorClip(size=(1080,1920),color=(5,0,0),duration=15)
    txt = TextClip(texto[:200],fontsize=100,color='yellow',font='DejaVu-Sans-Bold',size=(900,1600),method='caption')
    video = CompositeVideoClip([bg,txt.set_position("center")])
    video.set_audio(AudioFileClip(audio_p)).fx(vfx.lum_contrast,lum=1.03,contrast=1.1).write_videofile(
        OUT_PATH+"reel.mp4",fps=24,codec="libx264"
    )
    for i,f in enumerate(frases,1):
        img=Image.new('RGB',(1080,1080),(2,0,0))
        d=ImageDraw.Draw(img)
        d.rectangle([0,1070,(108*i),1080],fill="red")
        d.text((130,450),f"ALERTA {i}\n\n{f}",fill=(255,255,255))
        img.save(OUT_PATH+f"slide_{i}.jpg")

# ==========================================================
# 🚀 PUBLICAÇÃO
# ==========================================================

def publicar_v4(url_media,legenda):
    res=requests.post(
        f"https://graph.facebook.com/v20.0/{IG_ID}/media",
        data={"video_url":url_media,"media_type":"REELS","caption":legenda,"access_token":IG_TOKEN}
    ).json()
    creation_id=res.get("id")
    if creation_id:
        time.sleep(60)
        requests.post(
            f"https://graph.facebook.com/v20.0/{IG_ID}/media_publish",
            data={"creation_id":creation_id,"access_token":IG_TOKEN}
        )

# ==========================================================
# 🌐 WEBHOOK
# ==========================================================

@app.route('/webhook',methods=['GET'])
def verify():
    if request.args.get("hub.verify_token")==VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Erro",403

@app.route('/media/<path:filename>')
def serve(filename): return send_from_directory(OUT_PATH,filename)

# ==========================================================
# 🧠 NOVOS MOTORES & EVOLUTIVOS
# ==========================================================

RETENTION_WORDS=["ninguém","verdade","segredo","erro","alerta","proibido","revelado","chocante"]
EMOCOES={"curiosidade":["segredo","revelado","verdade"],"medo":["alerta","perigo","cuidado"],"raiva":["erro","mentira","enganado"]}

def score_retencao(texto):
    score=1.0
    for w in RETENTION_WORDS:
        if w in texto.lower(): score*=1.15
    if "?" in texto: score*=1.1
    return score

def score_emocional(texto):
    score=1.0
    t=texto.lower()
    for grupo in EMOCOES.values():
        for w in grupo:
            if w in t: score*=1.12
    return score

def prever_viralidade(hook):
    return score_dopamina(hook)*score_retencao(hook)*random.uniform(0.9,1.1)

def recomendar_tema():
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT tema,AVG(score) FROM posts GROUP BY tema ORDER BY AVG(score) DESC LIMIT 5")
    dados=c.fetchall()
    conn.close()
    return random.choice(dados)[0] if dados else radar_global()

def gerar_hook_otimizado(tema):
    hooks=[
        f"A verdade que ninguém aceita sobre {tema}",
        f"O erro silencioso em {tema}",
        f"O segredo oculto de {tema}",
        f"O alerta brutal sobre {tema}",
        f"O que nunca te contaram sobre {tema}",
        f"Isso pode mudar tudo em {tema}"
    ]
    melhor, melhor_score=None,0
    for h in hooks:
        score=prever_viralidade(h)*score_emocional(h)
        if score>melhor_score:
            melhor,melhor_score=h,score
    return melhor

def omega_brain():
    tema=recomendar_tema()
    hook=gerar_hook_otimizado(tema)
    score=prever_viralidade(hook)
    return tema,hook,score

# ==========================================================
# 📊 DASHBOARD
# ==========================================================

@app.route("/stats")
def stats():
    conn=sqlite3.connect(DB_PATH)
    c=conn.cursor()
    c.execute("SELECT COUNT(*) FROM posts")
    total=c.fetchone()[0]
    conn.close()
    return {"posts":total,"genes":GENES}

# ==========================================================
# 🛡 WATCHDOG
# ==========================================================

def safe_flask_run(app,port=5000):
    try: app.run(host='0.0.0.0',port=port)
    except Exception as e: print("ERRO FLASK:",e)

def safe_watchdog(app,port=5000,interval=300):
    def run():
        while True:
            try: requests.get(f"http://localhost:{port}")
            except: threading.Thread(target=lambda: safe_flask_run(app,port),daemon=True).start()
            threading.Event().wait(interval)
    threading.Thread(target=run,daemon=True).start()

# ==========================================================
# 🚀 CICLO VACINA / PUBLICAÇÃO INTELIGENTE
# ==========================================================

def evolve_genes(score,genes):
    if score>1.2: genes["zoom"]*=1.05; genes["contraste"]*=1.02
    else: genes["zoom"]*=0.97; genes["contraste"]*=0.99
    return genes

def instagram_manager(public_url,tema,hook):
    agora=datetime.datetime.now()
    trend_score=random.uniform(0.8,1.2)
    hora_certa=agora.hour in [6,8,10,12,14,16,18,20,22]
    if hora_certa and trend_score>0.9:
        try: fabricar_arsenal_v4000()
        except Exception as e: print("Erro fabricar:",e)
        try:
            legenda=motor_omni_v4000("Gere legenda viral")
            publicar_v4(f"{public_url}/media/reel.mp4",legenda)
        except Exception as e: print("Erro publicar:",e)
        print(f"[Manager] Publicado post/stories/DM: {tema} | {hook}")

def ciclo_vacina_cronificado(app,OUT_PATH,GENES):
    try:
        public_url=f"https://{os.environ.get('RENDER_EXTERNAL_URL','localhost')}"
        print("ACE ONLINE VACINA CRONIFICADO:",public_url)
        while True:
            agora=datetime.datetime.now()
            # Ciclo mestre automático
            if agora.hour in [6,8,10,12,14,16,18,20,22] and agora.minute==0:
                tema,hook,score=omega_brain()
                registrar_post(tema,hook,score)
                evolve_genes(score,GENES)
                instagram_manager(public_url,tema,hook)
                print(f"[Vacina] Post gerado: {tema} | Genes ajustados: {GENES}")
            # Stories automáticos em horários estratégicos
            if agora.hour in [7,19,22] and agora.minute==30:
                try: img_file = OUT_PATH+"slide_1.jpg"
                except: img_file = None
                if img_file: print(f"[Vacina] Story post: {img_file}")
            threading.Event().wait(60)
    except Exception as e: print("ERRO CICLO VACINA CRONIFICADO:",e)

# ==========================================================
# 🚀 START FINAL AUTOMÁTICO
# ==========================================================

if __name__=="__main__":
    threading.Thread(target=lambda: safe_flask_run(app,5000),daemon=True).start()
    safe_watchdog(app,5000)
    threading.Thread(target=lambda: ciclo_vacina_cronificado(app,OUT_PATH,GENES),daemon=True).start()
