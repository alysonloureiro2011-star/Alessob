from ace.engines.trend_engine import choose_trend, normalize_trend
from ace.engines.director_engine import choose_content_type, choose_style
from ace.engines.generator_engine import generate_hook, generate_body
from ace.engines.media_engine import build_media_package
from ace.engines.publish_engine import publish_media


def run_pipeline(trend=None):
    """
    Pipeline modular leve com compatibilidade ampliada.

    Regras:
    - Se trend vier vazio, usa choose_trend()
    - Se trend vier preenchido, usa esse valor
    - Tenta normalizar sem quebrar o fluxo
    - Mantém as chaves antigas
    - Adiciona chaves de compatibilidade úteis para integração futura
    """

    result = {}

    # 1) Trend
    if trend is None:
        trend = choose_trend()

    try:
        trend = normalize_trend(trend)
    except Exception:
        pass

    # 2) Decisão de formato/estilo
    content_type = choose_content_type()
    style = choose_style()

    # 3) Geração textual
    hook = generate_hook(trend, style)
    body = generate_body(trend, style)
    caption = f"{hook}\n\n{body}"

    # 4) Mídia
    media = build_media_package(trend, content_type, caption)

    # 5) Publicação
    publish = publish_media(media, caption)

    # 6) Chaves atuais
    result["trend"] = trend
    result["content_type"] = content_type
    result["style"] = style
    result["caption"] = caption
    result["media"] = media
    result["publish"] = publish

    # 7) Chaves de compatibilidade úteis
    result["plan"] = {
        "trend": trend,
        "content_type": content_type,
        "style": style,
    }

    result["content"] = {
        "hook": hook,
        "body": body,
        "caption": caption,
    }

    result["published"] = publish

    return result
