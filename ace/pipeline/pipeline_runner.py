from ace.engines.director_engine import build_director_plan
from ace.engines.generator_engine import build_content_package
from ace.engines.media_engine import build_media_package


def run_pipeline(trend):

    plan = build_director_plan(trend)

    content = build_content_package(
        trend=trend,
        style=plan["style"],
        content_type=plan["content_type"]
    )

    media = build_media_package(
        plan["content_type"],
        content["caption"]
    )

    return {
        "plan": plan,
        "content": content,
        "media": media
    }
