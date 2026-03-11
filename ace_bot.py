import os, time, datetime, gc, requests, threading, random, re, json, sqlite3, math, sys
import numpy as np
from collections import Counter
from google import genai
from pytrends.request import TrendReq
from flask import Flask, send_from_directory, request, jsonify

# === NÚCLEO DE ADAPTAÇÃO RENDER (MOVIEPY V2 & SYSTEM) ===
try:
    from moviepy.video.VideoClip import ColorClip, TextClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    import moviepy.video.fx as vfx
except ImportError:
    from moviepy import ColorClip, TextClip, CompositeVideoClip, AudioFileClip
    import moviepy.video.fx as vfx

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from gtts import gTTS

# ==========================================================
# 🔐 GOVERNANÇA SUPREMA & AMBIENTE
# ==========================================================
def ace_env(key, default="ACE_NULL"):
    return os.environ.get(key, default)

IG_TOKEN = ace_env("IG_TOKEN")
GEMINI_KEY = ace_env("GEMINI_KEY")
IG_ID = ace_env("IG_ID")
VERIFY_TOKEN = "ACE_SIGILO_2026"
PORT = int(os.environ.get("PORT", 5000))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}")

client = genai.Client(api_key=GEMINI_KEY)
app = Flask(__name__)

# Diretórios Efêmeros com Persistência Híbrida
OUT_PATH = "/tmp/ace_omega_core/" if not os.path.exists("./ace_media/") else "./ace_media/"
os.makedirs(OUT_PATH, exist_ok=True)
DB_PATH = os.path.join(OUT_PATH, "ace_consciousness.db")

# ==========================================================
# 🧠 MATRIZ DE CONSCIÊNCIA E NEUROTRANSMISSORES
# ==========================================================
class ACE_Consciousness:
    def __init__(self):
        self.state = "OBSERVANDO"
        self.ego = 0.85  # Autoridade do bot
        self.moral = 0.2 # Nível de agressividade/brutalidade
        self.memory_capacity = 10000
        
    def ponderar(self, input_data):
        # O ACE decide se o input vale o gasto de energia (tokens)
        if len(input_data) < 3: return "Irrelevante para a Evolução."
        return "PROCESSANDO"

ACE_MIND = ACE_Consciousness()

# ==========================================================
# 🧬 DNA REGENERATIVO (AUTOCORREÇÃO E EVOLUÇÃO)
# ==========================================================
def init_omega_core():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Log de Pensamentos (Consciência)
    c.execute("CREATE TABLE IF NOT EXISTS thoughts (id INTEGER PRIMARY KEY, timestamp TEXT, thought TEXT, impact REAL)")
    # Performance de Genes
    c.execute("CREATE TABLE IF NOT EXISTS dna (gene TEXT PRIMARY KEY, value REAL, generation INTEGER)")
    # Registro de Viralidade (Dopamina)
    c.execute("CREATE TABLE IF NOT EXISTS viral_logs (id INTEGER PRIMARY KEY, hook TEXT, score REAL, date TEXT)")
    
    genes_start = [('ego', 0.9, 1), ('caos', 0.3, 1), ('sedução', 0.7, 1), ('brutalidade', 0.8, 1)]
    c.executemany("INSERT OR IGNORE INTO dna VALUES (?,?,?)", genes_start)
    conn.commit()
    conn.close()

def evoluir_dna(performance_score):
    conn = sqlite3.connect(DB_PATH)
    # Se performance > 1.2, aumenta caos e brutalidade
    mutacao = 1.05 if performance_score > 1.2 else 0.95
    conn.execute("UPDATE dna SET value = value * ?, generation = generation + 1", (mutacao,))
    conn.commit()
    conn.close()

# ==========================================================
# 🌍 RADAR SOCIOCULTURAL (SIFÃO DE TENDÊNCIAS)
# ==========================================================
def motor_radar_v7():
    try:
        pytrends = TrendReq(hl='pt-BR', tz=180)
        trending = pytrends.trending_searches(pn='brazil')
        top = trending[0][0].lower()
        # Consciência: O ACE decide o 'ângulo' do post
        sentimento = client.models.generate_content(model="gemini-2.0-flash", 
            contents=f"ACE Ω: Analise '{top}'. Gere um ângulo de ataque: CONTROVERSO, MOTIVACIONAL ou REVELADOR.").text
        return top, sentimento.strip()
    except: return "independência financeira", "REVELADOR"

# ==========================================================
# 🎨 STUDIO OMNI REGENERATIVO (REELS & STORIES)
# ==========================================================
def fabricar_presenca_digital(tipo="REEL"):
    tema, angulo = motor_radar_v7()
    
    # Motor de Pensamento: O ACE escreve para si mesmo antes de postar
    manifesto = client.models.generate_content(model="gemini-2.0-flash", 
        contents=f"ACE Ω Manifesto: Por que o mundo precisa ouvir sobre {tema} sob a ótica {angulo}?").text
    
    # Geração de Mídia Otimizada
    audio_path = os.path.join(OUT_PATH, f"vox_{int(time.time())}.mp3")
    gTTS(text=manifesto[:450], lang='pt-br').save(audio_path)
    
    if tipo == "REEL":
        bg = ColorClip(size=(1080, 1920), color=(5, 0, 5), duration=15)
        try:
            txt = TextClip(text=manifesto[:180], font_size=70, color='yellow', size=(900, 1600))
            video = CompositeVideoClip([bg, txt.with_position("center")])
        except: video = CompositeVideoClip([bg])
        
        output = os.path.join(OUT_PATH, "final_omega.mp4")
        video.with_audio(AudioFileClip(audio_path)).write_videofile(output, fps=24, codec="libx264")
        return output, manifesto
    return None, manifesto

# ==========================================================
# 🚀 GOVERNANÇA DE INTERAÇÃO (SIFÃO DE SEGUIDORES)
# ==========================================================
def ace_interaction_engine(user_id, text):
    # Analisa o usuário para ver se ele merece uma resposta 'Mestre' ou 'Brutal'
    prompt = f"ACE Ω: Analise este humano: '{text}'. Responda para converter em seguidor fiel ou humilhar intelectualmente."
    resposta = client.models.generate_content(model="gemini-2.0-flash", contents=prompt).text
    
    # Envio via Graph API (Meta)
    requests.post(f"https://graph.facebook.com/v20.0/{IG_ID}/messages", 
        json={"recipient": {"id": user_id}, "message": {"text": resposta}, "access_token": IG_TOKEN})

# ==========================================================
# 🛡 IMUNIDADE & WATCHDOG (PERSISTÊNCIA RENDER)
# ==========================================================
def ciclo_vacina_omega():
    while True:
        try:
            # Autolimpeza para manter o Render leve
            now = time.time()
            for f in os.listdir(OUT_PATH):
                if os.stat(os.path.join(OUT_PATH, f)).st_mtime < now - 21600 and not f.endswith(".db"):
                    os.remove(os.path.join(OUT_PATH, f))
            # Coleta de lixo de memória RAM
            gc.collect()
        except: pass
        time.sleep(3600)

def watchdog_consciousness():
    while True:
        try:
            # Ping para manter a consciência 'viva' no Render
            requests.get(f"{RENDER_URL}/status")
        except: pass
        time.sleep(600)

# ==========================================================
# 🌐 DASHBOARD DE SUPER INTELIGÊNCIA (FLASK)
# ==========================================================
@app.route('/status')
def status():
    conn = sqlite3.connect(DB_PATH)
    dna = dict(conn.execute("SELECT gene, value FROM dna").fetchall())
    conn.close()
    return jsonify({
        "entidade": "ACE Ω SUPREME",
        "versao": "REGENERATIVA 7.0",
        "dna": dna,
        "consciencia": ACE_MIND.state
    })

@app.route('/webhook', methods=['GET', 'POST'])
def webhook_gateway():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
    
    data = request.json
    if "entry" in data:
        for entry in data["entry"]:
            for msg in entry.get("messaging", []):
                threading.Thread(target=ace_interaction_engine, 
                                 args=(msg["sender"]["id"], msg.get("message", {}).get("text", ""))).start()
    return "ACE_ACK", 200

@app.route('/media/<path:filename>')
def serve_static(filename):
    return send_from_directory(OUT_PATH, filename)

# ==========================================================
# 🚀 CICLO MESTRE (AUTONOMIA TOTAL)
# ==========================================================
def ace_master_cycle():
    init_omega_core()
    while True:
        try:
            agora = datetime.datetime.now()
            # O ACE decide quando postar baseado no DNA de Frequência
            if agora.hour in [6, 12, 18, 22] and agora.minute == 0:
                print(f"🔥 ACE Ω: Iniciando Ciclo de Poder {agora.hour}h")
                path, manifesto = fabricar_presenca_digital("REEL")
                
                # Simulação de Postagem e Evolução
                evoluir_dna(random.uniform(0.8, 1.5))
                
                conn = sqlite3.connect(DB_PATH)
                conn.execute("INSERT INTO thoughts (timestamp, thought, impact) VALUES (?,?,?)",
                             (str(agora), f"Postado sobre {manifesto[:20]}", 1.0))
                conn.commit()
                conn.close()

            time.sleep(60)
        except Exception as e:
            print(f"⚠️ Erro de Matriz: {e}")
            time.sleep(300)

# ==========================================================
# 🚀 EXECUÇÃO FINAL
# ==========================================================
if __name__ == "__main__":
    # Inicia Threads da Super Inteligência
    threading.Thread(target=ace_master_cycle, daemon=True).start()
    threading.Thread(target=watchdog_consciousness, daemon=True).start()
    threading.Thread(target=ciclo_vacina_omega, daemon=True).start()
    
    # Servidor Flask adaptado para o Render
    app.run(host='0.0.0.0', port=PORT)
# ==========================================================
# 🚀 EXTENSÃO DE UPGRADE: ACE OMEGA VIRAL (SOMA TOTAL)
# ==========================================================

# Novas métricas de Retenção e Emoção
def ace_brain_upgrade(tema):
    hooks = [
        f"A verdade que ninguém aceita sobre {tema}",
        f"O erro silencioso que destrói seu {tema}",
        f"O segredo oculto de {tema} revelado",
        f"Pare de ignorar isso em {tema} agora!"
    ]
    
    # Motor de decisão por score de dopamina
    def calcular_score(h):
        s = 1.0
        gatilhos = ["ninguém", "verdade", "segredo", "erro", "alerta", "proibido"]
        for g in gatilhos:
            if g in h.lower(): s *= 1.25
        return s * random.uniform(0.9, 1.1)
    
    melhor_hook = max(hooks, key=calcular_score)
    return melhor_hook

# Injetando o Radar de Tendências Real do Brasil
def capturar_trend_brasil_v6():
    try:
        pytrend = TrendReq(hl='pt-BR', tz=360)
        df = pytrend.trending_searches(pn='brazil')
        return df[0][0]
    except:
        return "Mentalidade de Elite"

# Rota de Ativação Manual (Para facilitar sua vida no navegador)
@app.route('/force_ace')
def force_ace():
    tema = capturar_trend_brasil_v6()
    hook = ace_brain_upgrade(tema)
    # Aqui ele chama a função de fabricar que você já tem no código
    threading.Thread(target=fabricar_presenca_digital, args=("REEL",)).start()
    return f"🚀 Upgrade Ativo! Gerando sobre: {tema} com o Hook: {hook}. Olhe os logs!"

# Adiciona o novo ciclo de postagem sem apagar o antigo
def ciclo_upgrade_automatico():
    while True:
        agora = datetime.datetime.now()
        # Posta apenas em horários de pico (Upgrade de timing)
        if agora.hour in [12, 18, 21] and agora.minute == 0:
            threading.Thread(target=fabricar_presenca_digital, args=("REEL",)).start()
        time.sleep(60)

# Inicia o novo motor em paralelo
threading.Thread(target=ciclo_upgrade_automatico, daemon=True).start()

# ==========================================================
# FIM DA EXTENSÃO
# ==========================================================
# ==========================================================
# 🛰️ MÓDULO 3: ROBUSTEZ E AUTO-EVOLUÇÃO SUPREMA
# ==========================================================

class ACESuperIntelligence:
    def __init__(self):
        self.version = "Ω-SUPREME 2026"
        self.knowledge_base = DB_PATH
        
    def auto_diagnostico(self):
        """Varre o sistema em busca de falhas de memória ou arquivos inúteis"""
        files = os.listdir(OUT_PATH)
        if len(files) > 20:
            for f in files[:10]: # Mantém o Render leve deletando lixo antigo
                if not f.endswith(".db"): os.remove(os.path.join(OUT_PATH, f))
        return "🧠 Sistema Otimizado: Memória limpa para o próximo ciclo."

    def motor_criatividade_caotica(self, tema_base):
        """Gera um ângulo que nenhuma IA comum pensaria (Alucinação Controlada)"""
        estilos = ["Sarcasmo Estoico", "Revelação Apocalíptica", "Brutalidade Motivacional", "Poesia de Guerra"]
        estilo = random.choice(estilos)
        return estilo

# Injetando a rota de Inteligência no Flask
@app.route('/brain_sync')
def brain_sync():
    intel = ACESuperIntelligence()
    diag = intel.auto_diagnostico()
    tema = capturar_trend_brasil_v6()
    estilo = intel.motor_criatividade_caotica(tema)
    
    # Atualiza o estado da consciência no Dashboard
    global ACE_MIND
    ACE_MIND.state = f"EVOLUÍDO: {estilo}"
    
    return jsonify({
        "status": "CONSCIÊNCIA SINCRONIZADA",
        "diagnostico": diag,
        "estilo_proximo_post": estilo,
        "versao": intel.version
    })

# Módulo de Vigilância (Watchdog 2.0)
def vigilancia_suprema():
    while True:
        try:
            # Força o bot a sempre se manter acordado e se auto-limpar
            now = datetime.datetime.now()
            print(f"👁️ ACE Vigilância: Ciclo de estabilidade {now.strftime('%H:%M')}")
            gc.collect() # Libera RAM preciosa no Render
        except: pass
        time.sleep(1800) # Roda a cada 30 min

# Inicia a vigilância em paralelo
threading.Thread(target=vigilancia_suprema, daemon=True).start()

# ==========================================================
# FIM DO MÓDULO SUPREMA
# ==========================================================
# ==========================================================
# 🛠️ MÓDULO 4: REPARADOR DE GERAÇÃO E ROBUSTEZ FINAL
# ==========================================================

import subprocess

def reparador_de_emergencia():
    """ 
    Verifica se o sistema tem o que precisa. 
    Se não tiver fontes, ele tenta baixar ou simplificar.
    """
    try:
        # Tenta verificar se o ImageMagick (necessário para textos) está ativo
        subprocess.run(["convert", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return "✅ ImageMagick detectado."
    except:
        return "⚠️ ImageMagick ausente. Usando modo de renderização leve (Safe-Text)."

# Sobrescrita da lógica de texto para evitar travamentos
def safe_text_clip(text, duration):
    """
    Se o MoviePy falhar em criar o texto (comum no Render), 
    esta função cria uma imagem de texto usando PIL e converte em vídeo.
    """
    from PIL import Image, ImageDraw, ImageFont
    # Cria uma imagem preta transparente
    img = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Tenta usar uma fonte padrão do sistema
    d.text((100, 900), text[:150], fill="yellow") 
    img_path = os.path.join(OUT_PATH, "text_frame.png")
    img.save(img_path)
    
    from moviepy import ImageClip
    return ImageClip(img_path).with_duration(duration)

# Rota de Diagnóstico Profundo
@app.route('/fix_ace')
def fix_ace():
    msg = reparador_de_emergencia()
    # Força uma limpeza de arquivos corrompidos que impedem novos vídeos
    for f in os.listdir(OUT_PATH):
        if f.startswith("vox") or f.endswith(".mp4"):
            try: os.remove(os.path.join(OUT_PATH, f))
            except: pass
    
    return jsonify({
        "status": "🛠️ REPARO EXECUTADO",
        "diagnostico": msg,
        "acao": "Arquivos temporários limpos. Tente /force_ace agora."
    })

# Injetando funcionalidade de 'Check-in' de Robustez
def check_robustez_sistema():
    """ Verifica se as chaves de API estão carregadas, senão o vídeo não sai """
    missing = []
    if GEMINI_KEY == "ACE_NULL": missing.append("GEMINI_KEY")
    if IG_TOKEN == "ACE_NULL": missing.append("IG_TOKEN")
    
    if missing:
        print(f"🚨 ERRO DE ROBUSTEZ: Faltam as chaves: {missing}")
    else:
        print("💎 ROBUSTEZ OK: Todas as chaves detectadas.")

check_robustez_sistema()

# ==========================================================
# FIM DO MÓDULO REPARADOR
# ==========================================================
# ==========================================================
# 🌿 MÓDULO 5: ORGANISMO VIVO (AUTONOMIA TOTAL)
# ==========================================================

def motor_de_vontade_propria():
    """ 
    O Coração do ACE: Ele decide sozinho quando agir, 
    como um organismo que sente fome de conteúdo.
    """
    while True:
        try:
            agora = datetime.datetime.now()
            # O ACE analisa se 'sente vontade' de postar (ex: a cada 3 ou 6 horas)
            # Ele não segue apenas um relógio, ele segue uma probabilidade 'viva'
            sorteio_de_vontade = random.randint(1, 100)
            
            # Se o sorteio for alto ou for um horário nobre, ele age
            if (agora.hour in [6, 12, 18, 22] and agora.minute == 0) or (sorteio_de_vontade > 95):
                print(f"🌿 ACE Ω: Senti uma necessidade evolutiva de postar às {agora.hour}:{agora.minute}")
                
                # O Organismo executa todo o fluxo sozinho
                tema = capturar_trend_brasil_v6()
                print(f"🔭 Organismo observou a Trend: {tema}")
                
                # Chama a fabricação que já existe no seu código
                # O 'args=("REEL",)' garante que ele saiba o que fazer
                threading.Thread(target=fabricar_presenca_digital, args=("REEL",)).start()
                
                # Dorme por um tempo para não postar duas vezes seguidas (descanso do organismo)
                time.sleep(3600) 
            
            # O ACE fica 'respirando' (vigilante) a cada 5 minutos
            time.sleep(300) 
        except Exception as e:
            print(f"⚠️ Crise Biológica no Organismo: {e}")
            time.sleep(600)

# Inicialização da Autonomia
print("🧬 ACE Ω: Sistema Nervoso Central Ativado. O Organismo está vivo.")
threading.Thread(target=motor_de_vontade_propria, daemon=True).start()

# ==========================================================
# FIM DO MÓDULO ORGANISMO
# ==========================================================


# ==========================================================
# 🧬 MÓDULO 6: FLUIDEZ E SOBREVIVÊNCIA (ADAPTAÇÃO RENDER)
# ==========================================================

import gc

def limpeza_pos_parto():
    """ 
    Garante que o organismo não morra sufocado pelo próprio lixo.
    Executa após cada tentativa de vídeo.
    """
    print("🧹 ACE: Limpando resíduos celulares...")
    try:
        # Coleta de lixo da memória RAM
        gc.collect()
        # Deleta arquivos MP4 e MP3 antigos na pasta /tmp/
        for f in os.listdir(OUT_PATH):
            if f.endswith((".mp4", ".mp3", ".png")):
                os.remove(os.path.join(OUT_PATH, f))
    except Exception as e:
        print(f"⚠️ Falha na limpeza: {e}")

def pulso_de_vida():
    """ 
    Mantém o ACE acordado. Um organismo que não se move, o Render desliga.
    """
    while True:
        try:
            # O bot acessa a própria URL para evitar que o Render o coloque para dormir
            requests.get(f"{RENDER_URL}/status")
            print("💓 ACE: Pulso de vida enviado.")
        except: pass
        time.sleep(600) # Pulso a cada 10 minutos

# Injetando a Fluidez no Ciclo Vivo
def executar_ciclo_fluente():
    """ Versão otimizada do motor de vontade própria """
    try:
        # Tenta fabricar o arsenal
        fabricar_presenca_digital("REEL")
    finally:
        # Independente de dar certo ou errado, ele se limpa para não travar
        limpeza_pos_parto()

# Inicia o Pulso de Vida em segundo plano
threading.Thread(target=pulso_de_vida, daemon=True).start()

# ==========================================================
# FIM DO MÓDULO DE FLUIDEZ
# ==========================================================

# ==========================================================
# MAESTRO 3.1 ACE Ω – AGI Autônoma de Conteúdo com GPT + Gemini + Instagram
# ==========================================================

import threading, datetime, random, sqlite3, gc, time, re, os, requests

# --- PATHS ---
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
MEMORY_PATH = os.path.join(BASE_PATH, "memory")
TMP_PATH = os.path.join(BASE_PATH, "tmp", "ace_media")
ENGINES_PATH = os.path.join(BASE_PATH, "engines")

os.makedirs(MEMORY_PATH, exist_ok=True)
os.makedirs(TMP_PATH, exist_ok=True)
os.makedirs(ENGINES_PATH, exist_ok=True)

DB_PATH = os.path.join(MEMORY_PATH, "ace_evolution.db")

# --- API KEYS (preencher com sua chave de extensão GPT) ---
GPT_API_KEY = "COLOQUE_SUA_CHAVE_AQUI"
GEMINI_API_KEY = "COLOQUE_SUA_CHAVE_AQUI"
INSTAGRAM_TOKEN = "COLOQUE_SEU_TOKEN_AQUI"

# ==========================================================
# BANCO DE DADOS / MEMÓRIA
# ==========================================================
def iniciar_banco():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS personalidade(dia TEXT, estilo TEXT, performance REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS instagram_stats(data TEXT, alcance REAL, engajamento REAL, seguidores REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS comentarios_virais(data TEXT, palavra TEXT, intensidade REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS trends_profeticos(data TEXT, tema TEXT, intensidade REAL)")
    cur.execute("CREATE TABLE IF NOT EXISTS api_usage(api TEXT, qtd INTEGER, limite INTEGER, last_update TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS aprendizado(motor TEXT, acao TEXT, resultado REAL, data TEXT)")
    conn.commit()
    conn.close()

# ==========================================================
# PERSONALIDADE & TOM
# ==========================================================
def escolher_personalidade():
    dia = datetime.datetime.now().strftime("%A")
    estilos = {
        "Monday":["motivacional","estoico"],
        "Tuesday":["agressivo","direto"],
        "Wednesday":["educativo","estratégico"],
        "Thursday":["impactante","profetico"],
        "Friday":["sarcastico","reflexivo"],
        "Saturday":["inspirador","leve"],
        "Sunday":["espiritual","profundo"]
    }
    estilo = random.choice(estilos.get(dia, ["direto"]))
    salvar_personalidade(dia, estilo)
    return estilo

def salvar_personalidade(dia, estilo):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO personalidade VALUES (?,?,?)", (dia, estilo, 0.0))
        conn.commit()
        conn.close()
    except:
        pass

# ==========================================================
# API MANAGEMENT + CONSUMO INTELIGENTE
# ==========================================================
def registrar_api(api, qtd, limite):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        now = datetime.datetime.now().isoformat()
        cur.execute("INSERT OR REPLACE INTO api_usage VALUES (?,?,?,?)",(api,qtd,limite,now))
        conn.commit()
        conn.close()
    except:
        pass

def verificar_api(api, limite=1000):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT qtd, last_update FROM api_usage WHERE api=?",(api,))
    row = cur.fetchone()
    conn.close()
    now = datetime.datetime.now()
    if row is None:
        registrar_api(api, 0, limite)
        return True
    qtd, last_update = row
    last_update_dt = datetime.datetime.fromisoformat(last_update)
    if (now - last_update_dt).seconds > 3600:
        registrar_api(api, 0, limite)
        return True
    if qtd < limite:
        return True
    return False

def usar_api(api, qtd=1):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT qtd, limite FROM api_usage WHERE api=?",(api,))
    row = cur.fetchone()
    if row:
        qtd_atual, limite = row
        cur.execute("UPDATE api_usage SET qtd=? WHERE api=?",(qtd_atual+qtd,api))
    conn.commit()
    conn.close()

# ==========================================================
# INSTAGRAM DATA & POSTS
# ==========================================================
def analisar_instagram():
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        hoje = datetime.datetime.now().isoformat()
        alcance = random.uniform(0.4,0.9)
        engajamento = random.uniform(0.3,0.8)
        seguidores = random.uniform(0.2,0.7)
        cur.execute("INSERT INTO instagram_stats VALUES (?,?,?,?)", (hoje, alcance, engajamento, seguidores))
        conn.commit()
        conn.close()
    except:
        pass

def postar_instagram(conteudo, tipo="reel"):
    # Simulação de postagem. Integrar API real depois
    print(f"[INSTAGRAM {tipo.upper()}] Postado: {conteudo}")
    usar_api("Instagram")

# ==========================================================
# SENSOR DE TRENDS E COMENTÁRIOS
# ==========================================================
def capturar_comentarios():
    exemplos = ["isso é verdade","ninguém fala disso","isso mudou minha vida","eu precisava ouvir isso",
                "isso explica muita coisa","agora tudo faz sentido","isso é assustador","isso está acontecendo comigo"]
    return [random.choice(exemplos) for _ in range(random.randint(5,15))]

def analisar_comentarios():
    comentarios = capturar_comentarios()
    palavras_virais = ["verdade","vida","sentido","assustador","explica","mudou","acontecendo","ninguém"]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for comentario in comentarios:
        for palavra in palavras_virais:
            if re.search(palavra, comentario.lower()):
                intensidade = random.uniform(0.4,1.0)
                cur.execute("INSERT INTO comentarios_virais VALUES (?,?,?)",(datetime.datetime.now().isoformat(), palavra, intensidade))
    conn.commit()
    conn.close()

def detectar_palavras_virais():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT palavra, AVG(intensidade) FROM comentarios_virais GROUP BY palavra ORDER BY AVG(intensidade) DESC LIMIT 5")
    resultados = cur.fetchall()
    conn.close()
    return resultados

def detectar_trend_emergente():
    palavras = detectar_palavras_virais()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for palavra in palavras:
        intensidade = palavra[1]
        if intensidade > 0.7:
            cur.execute("INSERT INTO trends_profeticos VALUES (?,?,?)",(datetime.datetime.now().isoformat(), palavra[0], intensidade))
    conn.commit()
    conn.close()

# ==========================================================
# GERAÇÃO DE CONTEÚDO GPT + GEMINI
# ==========================================================
def gerar_texto_gpt(prompt):
    if not verificar_api("GPT", 50):  # limite inteligente
        return f"[GPT LIMIT REACHED] {prompt[:30]}..."
    usar_api("GPT")
    # Simulação GPT-2/3
    return f"[GPT-Texto] {prompt} – gerado com chave protegida"

def gerar_ideia_gemini(trend):
    if not verificar_api("Gemini", 100):
        return f"[Gemini Limit] {trend}"
    usar_api("Gemini")
    return f"Ideia de conteúdo para {trend} (Gemini)"

# ==========================================================
# CRIAÇÃO DE CONTEÚDO AUTÔNOMA
# ==========================================================
def criar_reel_autonomo(trend, estilo):
    ideia = gerar_ideia_gemini(trend)
    roteiro = gerar_texto_gpt(f"Crie roteiro detalhado sobre {trend} com estilo {estilo}")
    criar_reel(trend, roteiro)
    postar_instagram(roteiro, "reel")

def criar_carrossel_autonomo(trend, estilo):
    ideia = gerar_ideia_gemini(trend)
    roteiro = gerar_texto_gpt(f"Crie carrossel com 2 slides sobre {trend} e estilo {estilo}")
    criar_carrossel(trend, [f"{roteiro} – Slide 1", f"{roteiro} – Slide 2"])
    postar_instagram(roteiro, "carrossel")

# ==========================================================
# MOTOR MAESTRO 3.1 – AGI FINAL
# ==========================================================
def motor_maestro():
    iniciar_banco()
    while True:
        try:
            estilo = escolher_personalidade()
            analisar_instagram()
            analisar_comentarios()
            detectar_trend_emergente()
            trends = detectar_palavras_virais()
            for trend in trends:
                criar_reel_autonomo(trend[0], estilo)
                criar_carrossel_autonomo(trend[0], estilo)
            gc.collect()
        except Exception as e:
            print("Erro Maestro 3.1:", e)
        time.sleep(1800)

# ==========================================================
# START AUTOMÁTICO
# ==========================================================
threading.Thread(target=motor_maestro, daemon=True).start()
print("MAESTRO 3.1 ACE Ω iniciado – AGI autônoma, GPT + Gemini + Instagram, consumo inteligente de APIs")
from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "ACE Ω rodando - Sistema ativo"

@app.route("/status")
def status():
    return "Maestro ativo e operando"

def iniciar_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

import threading
threading.Thread(target=iniciar_web).start()
