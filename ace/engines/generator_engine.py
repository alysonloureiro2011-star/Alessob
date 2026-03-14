def generate_hook(trend=None, style=None):
    trend = str(trend or "disciplina").strip()
    return f"O que quase ninguém percebe sobre {trend}"


def generate_body(trend=None, style=None, content_type=None):
    trend = str(trend or "disciplina").strip()
    style = str(style or "filosofico").strip()
    content_type = str(content_type or "reel").strip()

    return (
        f"Quase ninguém fala disso.\n\n"
        f"{trend.capitalize()} não nasce de intensidade curta.\n"
        f"Nasce de repetição certa.\n\n"
        f"Estilo: {style}\n"
        f"Formato: {content_type}\n\n"
        f"É aí que muita gente se perde."
    )


def generate_caption(trend=None, style=None, content_type=None):
    hook = generate_hook(trend, style)
    body = generate_body(trend, style, content_type)
    return f"{hook}\n\n{body}"


def build_content_package(trend, style, content_type):
    hook = generate_hook(trend, style)
    body = generate_body(trend, style, content_type)
    caption = generate_caption(trend, style, content_type)

    return {
        "hook": hook,
        "body": body,
        "caption": caption,
        "text": caption,
        "trend": trend,
        "style": style,
        "content_type": content_type,
    }


def generate_content(plan):
    trend = plan.get("trend")
    style = plan.get("style")
    content_type = plan.get("content_type")
    return build_content_package(trend, style, content_type)
