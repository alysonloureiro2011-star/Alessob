import random


MUTATION_PATTERNS = [

    "A verdade desconfortável sobre {trend}",
    "O erro que todo mundo comete com {trend}",
    "Por que quase ninguém entende {trend}",
    "O detalhe invisível sobre {trend}",
    "O que está por trás de {trend}",
    "O problema silencioso em {trend}",
]


def mutate_hook(trend):

    pattern = random.choice(MUTATION_PATTERNS)

    return pattern.format(trend=trend)
