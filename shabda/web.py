import asyncio
from shabda.dj import Dj
from flask import jsonify, send_from_directory


from flask import Blueprint, app

bp = Blueprint("web", __name__, url_prefix="/")

dj = Dj()


@bp.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@bp.route("/pack/<definition>")
async def pack(definition):
    tasks = []
    words = parse_definition(definition)
    for word, number in words.items():
        tasks.append(fetch_one(word, number))
    await asyncio.gather(*tasks)
    return f"Pack {definition} downloaded!"


@bp.route("/pack/<definition>.json")
async def pack_json(definition):
    words = parse_definition(definition)
    samples = []
    for word, number in words.items():
        samples = samples + dj.list(word, number)
    reslist = []
    for sample in samples:
        reslist.append({"url": "", "type": "audio", "bank": "", "n": ""})
    return jsonify(reslist)


@bp.route("/sample/<path:path>")
def sample(path):
    return send_from_directory("../samples/", path, as_attachment=False)


async def fetch_one(word, number):
    await dj.fetch(word, number)


def parse_definition(definition):
    words = {}
    sections = definition.split(",")
    for section in sections:
        parts = section.split(":")
        word = parts[0]
        if len(parts) > 1:
            number = int(parts[1])
        else:
            number = 5
        words[word] = number
    return words
