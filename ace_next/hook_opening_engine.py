"""
ACE Ω — Hook Opening Engine
Responsável pelos primeiros 3 segundos
"""

import random


def generate_hook_opening(trend, style=None, content_type=None):
    visual_hooks = [
        f"movimento brusco + zoom em {trend}",
        f"close extremo com expressão intensa sobre {trend}",
        f"mudança visual inesperada relacionada a {trend}",
        f"contraste forte antes/depois sobre {trend}",
    ]

    audio_hooks = [
        f"Você está fazendo isso errado com {trend}",
        f"Ninguém percebe isso sobre {trend}",
        f"Isso muda tudo sobre {trend}",
        f"Se você ignorar isso, vai se arrepender",
    ]

    text_hooks = [
        f"o erro invisível sobre {trend}",
        f"por que {trend} não funciona como você pensa",
        f"a verdade que ninguém fala sobre {trend}",
        f"isso explica tudo sobre {trend}",
    ]

    pattern_interrupts = [
        "zoom rápido",
        "corte seco",
        "mudança de ângulo",
        "efeito glitch leve",
    ]

    return {
        "visual_hook": random.choice(visual_hooks),
        "audio_hook": random.choice(audio_hooks),
        "text_hook": random.choice(text_hooks),
        "pattern_interrupts": random.sample(pattern_interrupts, 2),
        "intensity_score": round(random.uniform(0.70, 0.95), 2),
    }
