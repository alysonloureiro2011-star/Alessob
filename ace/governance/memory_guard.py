MAX_SCORE = 3.0

def normalize_memory(memory):

    for group in memory.values():
        for key, value in group.items():
            if value > MAX_SCORE:
                group[key] = MAX_SCORE
