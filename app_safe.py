from flask import Flask

from ace_next.official_app import create_official_app


app: Flask = create_official_app()
