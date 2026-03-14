import random

def choose_trend():
    trends = [
        "disciplina",
        "prosperidade",
        "renovação da mente",
        "clareza de propósito",
        "controle emocional",
        "mentalidade forte"
    ]
    return random.choice(trends)


def pick_trend():
    return choose_trend()


def get_trend():
    return choose_trend()
