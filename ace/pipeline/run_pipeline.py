from ace.engines.trend_engine import choose_trend, normalize_trend
from ace.engines.director_engine import choose_content_type, choose_style
from ace.engines.generator_engine import generate_hook, generate_body
from ace.engines.media_engine import build_media_package
from ace.engines.publish_engine import publish_media

def run_pipeline(trend=None):
    """
    Executa o pipeline modular ACE.

    Se um `trend` for passado, usa esse valor (depois tenta normalizá-lo).
    Caso contrário, escolhe uma tendência via `choose_trend()`.
    Retorna um dicionário contendo as chaves originais (trend, content_type, style,
    caption, media, publish) e também chaves de compatibilidade (plan, content, published).
    """

    result = {}

    # 1) Usar o trend fornecido ou selecionar automaticamente
    if trend is None:
        trend = choose_trend()

    # 2) Tentar normalizar o trend; se falhar, usa o valor original
    try:
        trend = normalize_trend(trend)
    except Exception:
        pass

    # 3) Escolher tipo de conteúdo e estilo
    content_type = choose_content_type()
    style = choose_style()

    # 4) Gerar hook e body
    hook = generate_hook(trend, style)
    body = generate_body(trend, style)

    # 5) Construir a legenda (caption)
    caption = f"{hook}\n\n{body}"

    # 6) Construir mídia e publicar
    media = build_media_package(trend, content_type, caption)
    publish = publish_media(media, caption)

    # 7) Preencher as chaves principais
    result["trend"] = trend
    result["content_type"] = content_type
    result["style"] = style
    result["caption"] = caption
    result["media"] = media
    result["publish"] = publish

    # 8) Chaves de compatibilidade (podem ser preenchidas futuramente)
    result["plan"] = None
    result["content"] = None
    result["published"] = None

    return result
