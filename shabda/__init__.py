"""Shabda init"""

from flask import Flask

from shabda.dj import Dj
from . import web


def create_app():
    """Create the Flask application"""
    app = Flask(__name__)

    app.register_blueprint(web.bp)

    return app


if __name__ == "__main__":
    print("Hello world")
