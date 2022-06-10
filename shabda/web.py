import asyncio
from shabda.dj import Dj
from flask import Blueprint, jsonify, send_from_directory, request
from urllib.parse import urlparse

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


@bp.route("/<definition>.json")
def pack_json(definition):
    url = urlparse(request.base_url)
    base = url.scheme + "://" + url.hostname
    if url.port:
        base += ":" + str(url.port)
    words = parse_definition(definition)
    reslist = []
    for word, number in words.items():
        samples = dj.list(word, number)
        n = 0
        for sample in samples:
            reslist.append(
                {
                    "url": sample,
                    "type": "audio",
                    "bank": word,
                    "n": n,
                }
            )
            n += 1

    return jsonify(reslist)


@bp.route("/samples/<path:path>")
def sample(path):
    return send_from_directory("../samples/", path, as_attachment=False)


@bp.after_request
def cors_after(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


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
            number = 1
        words[word] = number
    return words
