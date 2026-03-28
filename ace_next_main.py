from ace_next_official_main import app
from ace_next.config import load_config

if __name__ == '__main__':
    cfg = load_config()
    app.run(host='0.0.0.0', port=cfg.port)
