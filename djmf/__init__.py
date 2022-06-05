from flask import Flask
from djmf.dj import Dj


def create_app():
    app = Flask(__name__)

    from . import web

    app.register_blueprint(web.bp)

    return app


if __name__ == "__main__":
    print("Hello world")
