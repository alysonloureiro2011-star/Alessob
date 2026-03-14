def run_pipeline(trend):

    from ace.engines.generator_engine import build_content_package
    from ace.engines.media_engine import build_media_package

    content = build_content_package(
        trend=trend,
        style="filosofico",
        content_type="reel"
    )

    media = build_media_package(
        content_type="reel",
        caption=content.get("text","")
    )

    return {
        "trend": trend,
        "content": content,
        "media": media
    }
