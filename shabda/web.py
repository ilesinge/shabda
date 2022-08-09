"""Shabda web routes"""

import asyncio
from urllib.parse import urlparse
import json
import os
from zipfile import ZipFile
import tempfile
from flask import (
    Blueprint,
    jsonify,
    send_from_directory,
    request,
    render_template,
    send_file,
    after_this_request,
)
from werkzeug.exceptions import BadRequest, HTTPException
from shabda.dj import Dj


bp = Blueprint("web", __name__, url_prefix="/")

dj = Dj()


@bp.route("/")
def home():
    """Main page"""
    return render_template("home.html")


@bp.route("/pack/<definition>")
async def pack(definition):
    """Retrieve a pack of samples"""
    licenses = request.args.get("licenses")

    tasks = []
    words = parse_definition(definition)
    for word, number in words.items():
        if number is None:
            number = 1
        tasks.append(fetch_one(word, number, licenses))
    results = await asyncio.gather(*tasks)

    global_status = "empty"
    for status in results:
        if status is True:
            global_status = "ok"

    return jsonify(
        {
            "status": global_status,
            "definition": clean_definition(words),
        }
    )


@bp.route("/<definition>.json")
async def pack_json(definition):
    """Download a reslist definition"""
    complete = request.args.get("complete", False, type=bool)
    import pprint

    pprint.pprint(complete)

    await pack(definition)

    url = urlparse(request.base_url)
    base = url.scheme + "://" + url.hostname
    if url.port:
        base += ":" + str(url.port)
    words = parse_definition(definition)
    reslist = []
    for word, number in words.items():
        samples = dj.list(word, number)
        sample_num = 0
        for sampleurl in samples:
            reslist.append(
                {
                    "url": sampleurl,
                    "type": "audio",
                    "bank": word,
                    "n": sample_num,
                }
            )
            sample_num += 1

    return jsonify(reslist)


@bp.route("/<definition>.zip")
def pack_zip(definition):
    """Download a zip archive"""
    words = parse_definition(definition)
    definition = clean_definition(words)
    tmpfile = tempfile.gettempdir() + "/" + definition + ".zip"
    with ZipFile(tmpfile, "w") as zipfile:
        for word, number in words.items():
            samples = dj.list(word, number)
            for sample in samples:
                zipfile.write(sample, sample[len("samples/") :])

    @after_this_request
    def remove_file(response):
        os.remove(tmpfile)
        return response

    return send_file(tmpfile, as_attachment=True)


@bp.route("/samples/<path:path>")
def serve_sample(path):
    """Serve a sample"""
    return send_from_directory("../samples/", path, as_attachment=False)


@bp.route("/assets/<path:path>")
def static(path):
    """Serve a static asset"""
    return send_from_directory("../assets/", path, as_attachment=False)


@bp.errorhandler(HTTPException)
def handle_exception(exception):
    """Return JSON instead of HTML for HTTP errors."""
    # start with the correct headers and status code from the error
    response = exception.get_response()
    # replace the body with JSON
    response.data = json.dumps(
        {
            "code": exception.code,
            "name": exception.name,
            "description": exception.description,
        }
    )
    response.content_type = "application/json"
    return response


@bp.after_request
def cors_after(response):
    """Add CORS headers to response"""
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


async def fetch_one(word, number, licenses):
    """Fetch a single sample set"""
    return await dj.fetch(word, number, licenses)


def parse_definition(definition):
    """Parse a pack definition"""
    words = {}
    sections = definition.split(",")
    for section in sections:
        parts = section.split(":")
        rawword = parts[0]
        word = "".join(ch for ch in rawword if ch.isalnum())
        if len(word) == 0:
            raise BadRequest("A sample name is required")
        number = None
        if len(parts) > 1:
            try:
                number = int(parts[1])
            except ValueError as exception:
                raise BadRequest(
                    "A valid sample number is required after the colon"
                ) from exception
            if number < 1:
                raise BadRequest("A sample number must be greater than 0")
            if number > 10:
                raise BadRequest("A sample number must be less than 11")
        words[word] = number
    return words


def clean_definition(words):
    """reconstruct the definition without unwanted chars"""
    definition = []
    for word, number in words.items():
        definition.append(word + (":" + str(number) if number else ""))
    return ",".join(definition)
