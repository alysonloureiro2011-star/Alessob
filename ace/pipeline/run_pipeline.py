from ace.engines.trend_engine import choose_trend, normalize_trend
from ace.engines.director_engine import choose_content_type, choose_style
from ace.engines.generator_engine import generate_hook, generate_body
from ace.engines.media_engine import build_media_package
from ace.engines.publish_engine import publish_media


def run_pipeline():

    result = {}

    trend = choose_trend()
    trend = normalize_trend(trend)

    content_type = choose_content_type()
    style = choose_style()

    hook = generate_hook(trend, style)
    body = generate_body(trend, style)

    caption = f"{hook}\n\n{body}"

    media = build_media_package(trend, content_type, caption)

    publish = publish_media(media, caption)

    result["trend"] = trend
    result["content_type"] = content_type
    result["style"] = style
    result["caption"] = caption
    result["media"] = media
    result["publish"] = publish

    return result
