import asyncio
from shabda.dj import Dj
from flask import Blueprint, jsonify, send_from_directory, request, render_template
from werkzeug.exceptions import BadRequest, HTTPException
from urllib.parse import urlparse
import json

bp = Blueprint("web", __name__, url_prefix="/")

dj = Dj()


@bp.route("/")
def home():
    return render_template("home.html")


@bp.route("/pack/<definition>")
async def pack(definition):
    tasks = []
    words = parse_definition(definition)
    for word, number in words.items():
        tasks.append(fetch_one(word, number))
    await asyncio.gather(*tasks)
    return jsonify(
        {
            "status": "ok",
            "definition": definition,
        }
    )


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
        for sampleurl in samples:
            reslist.append(
                {
                    "url": sampleurl,
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


@bp.route("/assets/<path:path>")
def static(path):
    return send_from_directory("../assets/", path, as_attachment=False)


@bp.errorhandler(HTTPException)
def handle_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = e.get_response()
    # replace the body with JSON
    response.data = json.dumps(
        {
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }
    )
    response.content_type = "application/json"
    return response


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
        if len(word) == 0:
            raise BadRequest("A sample name is required")
        number = 1
        if len(parts) > 1:
            try:
                number = int(parts[1])
            except ValueError:
                raise BadRequest("A valid sample number is required after the colon")
            if number < 1:
                raise BadRequest("A sample number must be greater than 0")
            if number > 10:
                raise BadRequest("A sample number must be less than 11")
        words[word] = number
    return words
