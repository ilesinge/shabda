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
    if licenses is not None:
        licenses = licenses.split(",")

    tasks = []
    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        raise BadRequest(ex) from ex

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
    licenses = request.args.get("licenses", None)
    if licenses is not None:
        licenses = licenses.split(",")

    await pack(definition)

    url = urlparse(request.base_url)
    base = url.scheme + "://" + url.hostname
    if url.port:
        base += ":" + str(url.port)
    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        raise BadRequest(ex) from ex
    reslist = []
    for word, number in words.items():
        samples = dj.list(word, number, licenses=licenses)
        sample_num = 0
        for sound in samples:
            sound_data = {
                "url": sound.file,
                "type": "audio",
                "bank": word,
                "n": sample_num,
            }
            if complete:
                sound_data["licensename"] = sound.licensename
                sound_data["original_url"] = sound.url
                sound_data["author"] = sound.username
            reslist.append(sound_data)
            sample_num += 1

    return jsonify(reslist)


@bp.route("/<definition>.zip")
def pack_zip(definition):
    """Download a zip archive"""
    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        raise BadRequest(ex) from ex
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


@bp.route("/speech/<definition>")
async def speech(definition):
    """Download a spoken word"""
    gender = request.args.get("gender", "f")
    language = request.args.get("language", "en-GB")

    definition = definition.replace(" ", "_")
    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        raise BadRequest(ex) from ex
    tasks = []
    for word in words:
        tasks.append(speak_one(word, language, gender))
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


@bp.route("/speech/<definition>.json")
async def speech_json(definition):
    """Download a reslist definition"""
    gender = request.args.get("gender", "f")
    language = request.args.get("language", "en-GB")
    definition = definition.replace(" ", "_")

    await speech(definition)

    url = urlparse(request.base_url)
    base = url.scheme + "://" + url.hostname
    if url.port:
        base += ":" + str(url.port)
    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        raise BadRequest(ex) from ex
    reslist = []
    for word in words:
        samples = dj.list(word, gender=gender, language=language, soundtype="tts")
        sample_num = 0
        for sound in samples:
            sound_data = {
                "url": sound.file,
                "type": "audio",
                "bank": word,
                "n": sample_num,
            }
            reslist.append(sound_data)
            sample_num += 1

    return jsonify(reslist)


@bp.route("speech/speech_samples/<path:path>")
def serve_sample(path):
    """Serve a sample"""
    return send_from_directory("../speech_samples/", path, as_attachment=False)


@bp.route("/samples/<path:path>")
def serve_speech_sample(path):
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


async def speak_one(word, language, gender):
    """Speak a word"""
    return await dj.speak(word, language, gender)


async def fetch_one(word, number, licenses):
    """Fetch a single sample set"""
    return await dj.fetch(word, number, licenses)


def clean_definition(words):
    """reconstruct the definition without unwanted chars"""
    definition = []
    for word, number in words.items():
        definition.append(word + (":" + str(number) if number else ""))
    return ",".join(definition)
