from ace.engines.creative_brain import build_authorial_text


def build_content_package(trend, style, content_type):
    return build_authorial_text(
        trend=trend,
        style=style,
        content_type=content_type
    )
