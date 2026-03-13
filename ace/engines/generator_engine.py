def generate_hook(trend):
    return f"A verdade que ninguém aceita sobre {trend}"


def generate_body(trend, style, content_type):
    return (
        f"Tema: {trend}\n"
        f"Estilo: {style}\n"
        f"Formato: {content_type}\n\n"
        f"Esse é o conteúdo inicial gerado para o ACE."
    )


def build_content_package(trend, style, content_type):
    hook = generate_hook(trend)
    body = generate_body(trend, style, content_type)

    return {
        "hook": hook,
        "body": body,
        "caption": f"{hook}\n\n{body}"
    }
