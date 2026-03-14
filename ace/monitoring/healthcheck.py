import os

def ace_health():

    return {
        "media_dir": os.path.exists("ace_media"),
        "logs": os.path.exists("logs"),
        "status": "ok"
    }
