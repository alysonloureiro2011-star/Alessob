import random


def generate_hook(trend):
    hooks = [
        f"A verdade que ninguém aceita sobre {trend}",
        f"O erro que todo mundo comete quando fala de {trend}",
        f"O lado oculto de {trend} que ninguém explica",
        f"Por que {trend} está enganando tanta gente",
        f"O que realmente está acontecendo com {trend}",
    ]
    return random.choice(hooks)


def generate_body(trend, style, content_type):
    return (
        f"Tema: {trend}\n"
        f"Estilo: {style}\n"
        f"Formato: {content_type}\n\n"
        f"Esse é o conteúdo inicial gerado pelo ACE."
    )


def build_content_package(trend, style, content_type):
    hook = generate_hook(trend)
    body = generate_body(trend, style, content_type)

    return {
        "hook": hook,
        "body": body,
        "caption": f"{hook}\n\n{body}",
    }
