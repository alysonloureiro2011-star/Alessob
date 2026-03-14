import hashlib

SEEN_CONTENT = set()

def is_duplicate(text):

    key = hashlib.md5(text.encode()).hexdigest()

    if key in SEEN_CONTENT:
        return True

    SEEN_CONTENT.add(key)

    return False
