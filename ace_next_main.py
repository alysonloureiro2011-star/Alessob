from ace_next.official_app import create_official_app
from ace_next.config import load_config

app = create_official_app()

if __name__ == '__main__':
    cfg = load_config()
    app.run(host='0.0.0.0', port=cfg.port)
