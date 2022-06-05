from pprint import pprint
import asyncio
from djmf.dj import Dj


from flask import Blueprint, app

bp = Blueprint("web", __name__, url_prefix="/")

dj = Dj()


@bp.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@bp.route("/pack/<definition>")
async def pack(definition):
    sections = definition.split(",")
    tasks = []
    for section in sections:
        parts = section.split(":")
        word = parts[0]
        if len(parts) > 1:
            number = int(parts[1])
        else:
            number = 5
        tasks.append(fetch_one(word, number))
    await asyncio.gather(*tasks)
    return f"Pack {definition} downloaded!"


async def fetch_one(word, number):
    await dj.fetch(word, number)
