from ace.engines.trend_engine import choose_trend, normalize_trend
from ace.engines.director_engine import choose_content_type, choose_style
from ace.engines.generator_engine import generate_hook, generate_body
from ace.engines.media_engine import build_media_package
from ace.engines.publish_engine import publish_media

try:
    from ace.engines.living_myth_engine import myth_run_cycle
except Exception:
    myth_run_cycle = None


def run_pipeline(trend=None):
    """
    Pipeline modular oficial do ACE Ω com integração leve do Living Myth Engine.

    Regras:
    - Se trend vier vazio, usa choose_trend()
    - Se trend vier preenchido, usa esse valor
    - Tenta normalizar o trend sem quebrar o fluxo
    - Executa o Living Myth Engine como camada consultiva
    - Mantém as chaves antigas
    - Adiciona chaves ricas para evolução futura
    """

    result = {}

    # 1) Trend
    if trend is None:
        trend = choose_trend()

    try:
        trend = normalize_trend(trend)
    except Exception:
        pass

    # 2) Living Myth Engine (camada consultiva, nunca bloqueante)
    myth = None
    if myth_run_cycle is not None:
        try:
            myth = myth_run_cycle(trend)
        except Exception:
            myth = None

    # 3) Decisão de formato e estilo
    content_type = choose_content_type()
    style = choose_style()

    # 4) Geração textual principal
    hook = generate_hook(trend, style)
    body = generate_body(trend, style)
    caption = f"{hook}\n\n{body}"

    # 5) Mídia e publicação
    media = build_media_package(trend, content_type, caption)
    publish = publish_media(media, caption)

    # 6) Chaves clássicas
    result["trend"] = trend
    result["content_type"] = content_type
    result["style"] = style
    result["caption"] = caption
    result["media"] = media
    result["publish"] = publish

    # 7) Chaves ricas de compatibilidade
    result["plan"] = {
        "trend": trend,
        "content_type": content_type,
        "style": style,
        "myth_direction": myth.get("narrative_direction") if myth else None,
        "myth_tension": myth.get("dominant_tension") if myth else None,
        "myth_stage": myth.get("chapter_stage") if myth else None,
    }

    result["content"] = {
        "hook": hook,
        "body": body,
        "caption": caption,
        "narrative_direction": myth.get("narrative_direction") if myth else None,
        "symbolic_anchor": myth.get("symbolic_anchor") if myth else None,
        "cta_mode": myth.get("cta_mode") if myth else None,
    }

    result["published"] = publish

    # 8) Saída completa do myth engine
    result["myth"] = myth

    return result
