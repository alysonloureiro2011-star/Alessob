from ace.engines.trend_engine import build_trend_object
from ace.engines.director_engine import build_director_plan
from ace.engines.generator_engine import build_content_package
from ace.engines.media_engine import build_media_package
from ace.engines.publish_engine import publish_content


def run_modular_pipeline(trend):

    plan = build_director_plan(trend)

    content_type = plan["content_type"]
    style = plan["style"]

    content = build_content_package(
        trend=trend,
        style=style,
        content_type=content_type
    )

    media = build_media_package(
        content_type=content_type,
        caption=content["caption"]
    )

    published = publish_content(
        trend=trend,
        style=style,
        content_type=content_type,
        caption=content["caption"],
        media_path=media["media_path"]
    )

    return {
        "plan": plan,
        "content": content,
        "media": media,
        "published": published
    }


def run_test_pipeline():
    trend_obj = build_trend_object("inteligencia artificial", 1.0)
    trend = trend_obj["topic"]
    return run_modular_pipeline(trend)
