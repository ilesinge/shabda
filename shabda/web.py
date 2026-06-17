"""Shabda web routes"""

import asyncio
import os
from urllib.parse import urlparse
import json
import re
import pronouncing
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
from shabda.client import FreesoundUnavailableError
import shabda.phonemize as phonemize


SHABDA_PATH = os.path.expanduser("~/.shabda/")

SAMPLES_PATH = "samples/"
SPEECH_SAMPLE_PATH = "speech_samples/"

bp = Blueprint("web", __name__, url_prefix="/")

dj = Dj(SHABDA_PATH, SAMPLES_PATH, SPEECH_SAMPLE_PATH)
_phoneme_response_cache = {}


def safe_bank_name(name: str, preserve_underscores: bool = False) -> str:
    """Normalize a token into a bank-safe key.

    Words use hyphens, while phone sequence keys can preserve underscores.
    """
    name = name.strip()
    if preserve_underscores:
        name = re.sub(r"\s+", "-", name)
        name = re.sub(r"[^A-Za-z0-9_-]+", "-", name)
        name = re.sub(r"_+", "_", name)
        name = re.sub(r"-+", "-", name)
        return name.strip("-_")

    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"[^A-Za-z0-9-]+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def parse_arpabet_overrides(raw: str | None) -> dict[str, list[str]]:
    """Parse ARPABET overrides from query string.

    Format:
      overrides=word:PH1_PH2_PH3;other:PH1 PH2

    Notes:
      - entries are separated by ';'
      - phones may be separated by '_' or whitespace
      - words are matched case-insensitively
    """
    if not raw:
        return {}

    overrides = {}
    entries = [entry.strip() for entry in raw.split(";") if entry.strip()]
    for entry in entries:
        if ":" not in entry:
            continue
        word, phones_raw = entry.split(":", 1)
        word = "".join(ch for ch in word.lower().strip() if ch.isalnum())
        if not word:
            continue

        phones = [
            token.upper()
            for token in re.split(r"[_\s]+", phones_raw.strip())
            if token.strip()
        ]
        if not phones:
            continue

        overrides[word] = phones

    return overrides


def sentence_chunk_plan(sentence_word_phones):
    """Build a chunk plan where word boundaries remain sample boundaries."""
    plan = []
    for word, phones in sentence_word_phones:
        if not phones:
            plan.append(("oov", word))
            continue

        # Keep each word isolated so short unstressed words like "a" remain
        # their own sample, while stressed syllables still begin the chunk.
        for chunk in phonemize.chunk_phones_pre_stress(phones):
            chunk_key_raw = "phc_" + "_".join(chunk)
            plan.append(("chunk", chunk, word, chunk_key_raw))

    return plan


def sentence_tokens_to_timed_lines(
    tokens: list[str],
    beats_per_bar: int = 4,
    bars_per_line: int = 2,
    lead_in_beats: int | None = None,
    target_stress_beat: int = 3,
) -> list[str]:
    """Pad tokens into fixed-size lines and place stressed chunks on strong beats."""
    beats_per_bar = max(1, beats_per_bar)
    bars_per_line = max(1, bars_per_line)
    target_stress_beat = max(1, min(target_stress_beat, beats_per_bar))
    slots_per_line = beats_per_bar * bars_per_line

    if not tokens:
        return [" ".join(["~"] * slots_per_line)]

    def is_stressed_token(token: str) -> bool:
        return bool(re.search(r"[A-Z]+[12](?:_|$)", token))

    # Strong beats per bar: downbeat and (for 4/4-like meters) mid-bar accent.
    strong_offsets = [0]
    if beats_per_bar >= 4 and beats_per_bar % 2 == 0:
        strong_offsets.append(beats_per_bar // 2)

    strong_slots = []
    for bar in range(bars_per_line):
        bar_start = bar * beats_per_bar
        for offset in strong_offsets:
            slot = bar_start + offset
            if 0 <= slot < slots_per_line:
                strong_slots.append(slot)

    def next_strong_slot(position: int) -> int | None:
        for slot in strong_slots:
            if slot >= position:
                return slot
        return None

    # Build groups: stressed token plus following unstressed tokens stays together.
    groups = []
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if is_stressed_token(token):
            group = [token]
            idx += 1
            while idx < len(tokens) and not is_stressed_token(tokens[idx]):
                group.append(tokens[idx])
                idx += 1
            groups.append((True, group))
        else:
            group = [token]
            idx += 1
            while idx < len(tokens) and not is_stressed_token(tokens[idx]):
                group.append(tokens[idx])
                idx += 1
            groups.append((False, group))

    lines = []
    line_tokens = []
    group_i = 0

    if lead_in_beats is not None:
        forced_lead = max(0, lead_in_beats)
        line_tokens.extend(["~"] * min(forced_lead, slots_per_line))

    while group_i < len(groups):
        is_stress_group, group = groups[group_i]
        cursor = len(line_tokens)

        if is_stress_group:
            target_slot = next_strong_slot(cursor)
            if target_slot is None:
                line_tokens.extend(["~"] * (slots_per_line - len(line_tokens)))
                lines.append(" ".join(line_tokens))
                line_tokens = []
                continue

            needed_rests = max(0, target_slot - cursor)
            if cursor + needed_rests + len(group) > slots_per_line:
                line_tokens.extend(["~"] * (slots_per_line - len(line_tokens)))
                lines.append(" ".join(line_tokens))
                line_tokens = []
                continue

            line_tokens.extend(["~"] * needed_rests)
            line_tokens.extend(group)
            group_i += 1
            continue

        # Unstressed/OOV group: pack directly, split only if needed.
        available = slots_per_line - cursor
        if len(group) <= available:
            line_tokens.extend(group)
            group_i += 1
        else:
            if available > 0:
                line_tokens.extend(group[:available])
                groups[group_i] = (False, group[available:])
            line_tokens.extend(["~"] * (slots_per_line - len(line_tokens)))
            lines.append(" ".join(line_tokens))
            line_tokens = []

        if len(line_tokens) == slots_per_line:
            lines.append(" ".join(line_tokens))
            line_tokens = []

    if line_tokens:
        line_tokens.extend(["~"] * (slots_per_line - len(line_tokens)))
        lines.append(" ".join(line_tokens))

    return lines


def normalize_phoneme_definition(definition: str) -> str:
    """Normalize textarea input into the phoneme API definition format."""
    definition = definition.strip().lower()
    definition = re.sub(r"\r?\n+", ",", definition)
    definition = re.sub(r"\s*,\s*", ",", definition)
    definition = re.sub(r"[ \t]+", "_", definition)
    definition = re.sub(r"[^a-z0-9_,]+", "", definition)
    definition = re.sub(r"_+", "_", definition)
    definition = re.sub(r",+", ",", definition)
    return definition.strip("_,")


def parse_bool_arg(name: str, default: bool = False) -> bool:
    """Parse query bools robustly (supports 1/0, true/false, yes/no, on/off)."""
    raw = request.args.get(name)
    if raw is None:
        return default
    value = str(raw).strip().lower()
    if value in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "f", "no", "n", "off", ""}:
        return False
    return default


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

    for result in results:
        if isinstance(result, dict) and result.get("unavailable"):
            return jsonify(
                {
                    "status": "freesound_unavailable",
                    "error": result["error"],
                }
            ), 503

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
    complete = parse_bool_arg("complete", False)
    licenses = request.args.get("licenses", None)
    strudel = parse_bool_arg("strudel", False)
    if licenses is not None:
        licenses = licenses.split(",")

    await pack(definition)

    url = urlparse(request.base_url)
    scheme = url.scheme if url.hostname in ("localhost", "127.0.0.1") else "https"
    base = scheme + "://" + url.hostname
    if url.port:
        base += ":" + str(url.port)
    base += "/"
    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        raise BadRequest(ex) from ex
    if strudel:
        reslist = {"_base": base}
    else:
        reslist = []
    for word, number in words.items():
        samples = dj.list(word, number, licenses=licenses)
        sample_num = 0
        for sound in samples:
            if strudel:
                if word not in reslist:
                    reslist[word] = []
                reslist[word].append(sound.file)
            else:
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
                zipfile.write(sample.file, sample.file[len("samples/") :])

    @after_this_request
    def remove_file(response):
        os.remove(tmpfile)
        return response

    return send_file(tmpfile, as_attachment=True)


@bp.route("/speech/<definition>.zip")
def speech_zip(definition):
    """Download a zip archive"""
    definition = definition.replace(" ", "_")
    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        raise BadRequest(ex) from ex
    tmpfile = tempfile.gettempdir() + "/" + definition + ".zip"
    with ZipFile(tmpfile, "w") as zipfile:
        for word, number in words.items():
            samples = dj.list(word, number, soundtype="tts")
            for sample in samples:
                zipfile.write(sample.file, sample.file[len("speech_samples/") :])

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
    force = parse_bool_arg("force", False)

    definition = definition.replace(" ", "_")
    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        raise BadRequest(ex) from ex
    tasks = []
    for word in words:
        tasks.append(speak_one(word, language, gender, force=force))
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


async def _generate_phoneme_samples(definition, language, gender, force, overrides):
    """Synthesise all samples needed for a definition string."""
    sentence_definitions = [part for part in definition.split(",") if part]
    sentence_word_phones = [
        phonemize.sentence_to_arpabet(sentence_def, overrides=overrides)
        for sentence_def in sentence_definitions
    ]

    tasks = []
    seen_chunks = set()
    for sentence in sentence_word_phones:
        for unit in sentence_chunk_plan(sentence):
            unit_type = unit[0]
            if unit_type == "oov":
                value = unit[1]
                tasks.append(
                    speak_one(safe_bank_name(value), language, gender, force=force)
                )
                continue

            chunk = unit[1]
            text_hint = unit[2]
            chunk_key_raw = unit[3]
            chunk_key = safe_bank_name(chunk_key_raw, preserve_underscores=True)
            if chunk_key not in seen_chunks:
                seen_chunks.add(chunk_key)
                chunk_ipa = [phonemize.arpabet_to_ipa(phone) for phone in chunk]
                tasks.append(
                    speak_phoneme_chunk_one(
                        chunk_key,
                        chunk_ipa,
                        language,
                        gender,
                        text_hint=text_hint,
                        force=force,
                    )
                )

    await asyncio.gather(*tasks)
    return sentence_word_phones


async def build_phoneme_sentence_data(definition, overrides):
    """Build phoneme metadata without synthesising audio."""
    sentence_definitions = [part for part in definition.split(",") if part]
    sentence_word_phones = [
        phonemize.sentence_to_arpabet(sentence_def, overrides=overrides)
        for sentence_def in sentence_definitions
    ]

    return sentence_word_phones


def collect_phoneme_banks(sentence_word_phones):
    """Collect unique TTS bank keys needed for a phoneme definition."""
    banks = []
    seen = set()

    for sentence in sentence_word_phones:
        for word, phones in sentence:
            if phones is None:
                bank = safe_bank_name(word)
                if bank and bank not in seen:
                    seen.add(bank)
                    banks.append(bank)

        for unit in sentence_chunk_plan(sentence):
            if unit[0] != "chunk":
                continue
            chunk_key_raw = unit[3]
            bank = safe_bank_name(chunk_key_raw, preserve_underscores=True)
            if bank and bank not in seen:
                seen.add(bank)
                banks.append(bank)

    return banks


def speech_sample_zip_path(sample_file):
    """Return a stable relative zip path for speech sample files."""
    marker = SPEECH_SAMPLE_PATH
    if marker in sample_file:
        return sample_file.split(marker, 1)[1]
    return os.path.basename(sample_file)


@bp.route("/phonemes/<definition>")
async def phonemes(definition):
    """Generate phoneme samples for a sentence"""
    gender = request.args.get("gender", "f")
    language = request.args.get("language", "en-GB")
    force = parse_bool_arg("force", False)
    overrides = parse_arpabet_overrides(request.args.get("overrides"))

    definition = normalize_phoneme_definition(definition)
    sentence_word_phones = await _generate_phoneme_samples(
        definition, language, gender, force, overrides
    )
    word_phones = [item for sentence in sentence_word_phones for item in sentence]

    global_status = "empty"
    words_out = []
    phonemes_out = []
    for word, phones in word_phones:
        if phones is None:
            words_out.append(word)
            phonemes_out.append([word])   # single-element list signals OOV
        else:
            words_out.append(word)
            phonemes_out.append(phones)
            global_status = "ok"
        if phones:
            global_status = "ok"

    return jsonify(
        {
            "status": global_status,
            "words": words_out,
            "phonemes": phonemes_out,
        }
    )


@bp.route("/phonemes/<definition>.zip")
async def phonemes_zip(definition):
    """Download a zip archive for generated phoneme/OOV speech samples."""
    gender = request.args.get("gender", "f")
    language = request.args.get("language", "en-GB")
    force = parse_bool_arg("force", False)
    overrides = parse_arpabet_overrides(request.args.get("overrides"))

    definition = normalize_phoneme_definition(definition)
    sentence_word_phones = await _generate_phoneme_samples(
        definition, language, gender, force, overrides
    )

    banks = collect_phoneme_banks(sentence_word_phones)

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_handle:
        tmpfile = tmp_handle.name

    with ZipFile(tmpfile, "w") as zipfile:
        added = set()
        for bank in banks:
            samples = dj.list(bank, gender=gender, language=language, soundtype="tts")
            for sample in samples:
                if not sample.file or not os.path.exists(sample.file):
                    continue
                arcname = speech_sample_zip_path(sample.file)
                if arcname in added:
                    break
                zipfile.write(sample.file, arcname)
                added.add(arcname)
                break

    @after_this_request
    def remove_file(response):
        os.remove(tmpfile)
        return response

    return send_file(tmpfile, as_attachment=True)


@bp.route("/phonemes/<definition>.json")
async def phonemes_json(definition):
    """Return ordered phoneme sequence for reconstructing the sentence"""
    strudel = parse_bool_arg("strudel", False)
    details = parse_bool_arg("details", False)
    gender = request.args.get("gender", "f")
    language = request.args.get("language", "en-GB")
    beats_per_bar = request.args.get("beats_per_bar", 4, type=int)
    bars_per_line = request.args.get("bars_per_line", 2, type=int)
    lead_in_beats = request.args.get("lead_in_beats", type=int)
    target_stress_beat = request.args.get("target_stress_beat", 3, type=int)
    preview = parse_bool_arg("preview", False)
    overrides_raw = request.args.get("overrides")
    overrides = parse_arpabet_overrides(overrides_raw)
    force = parse_bool_arg("force", False)
    definition = normalize_phoneme_definition(definition)

    response_cache_key = (
        definition,
        strudel,
        details,
        preview,
        gender,
        language,
        beats_per_bar,
        bars_per_line,
        lead_in_beats,
        target_stress_beat,
        json.dumps(overrides, sort_keys=True),
    )

    if not force:
        cached_response = _phoneme_response_cache.get(response_cache_key)
        if cached_response is not None:
            return jsonify(cached_response)

    if preview:
        sentence_word_phones = await build_phoneme_sentence_data(definition, overrides)
    else:
        # Ensure all samples exist (with correct overrides and force flag)
        sentence_word_phones = await _generate_phoneme_samples(
            definition, language, gender, force, overrides
        )

    url = urlparse(request.base_url)
    scheme = url.scheme if url.hostname in ("localhost", "127.0.0.1") else "https"
    base = scheme + "://" + url.hostname
    if url.port:
        base += ":" + str(url.port)
    base += "/"
    word_phones = [item for sentence in sentence_word_phones for item in sentence]

    sentences_phonetic = []
    for sentence in sentence_word_phones:
        sentence_words = []
        for word, phones in sentence:
            if phones:
                arpabet_string = " ".join(phones)
                sentence_words.append(
                    {
                        "word": word,
                        "arpabet": arpabet_string,
                        "ipa": "".join(phonemize.arpabet_to_ipa(phone) for phone in phones),
                        "stress_pattern": pronouncing.stresses(arpabet_string),
                        "stressed_arpabet": [
                            phone for phone in phones if phone[-1:].isdigit() and phone[-1] in ("1", "2")
                        ],
                    }
                )
            else:
                sentence_words.append(
                    {
                        "word": word,
                        "arpabet": None,
                        "ipa": None,
                        "stress_pattern": None,
                        "stressed_arpabet": [],
                    }
                )
        sentences_phonetic.append(sentence_words)

    sentences_strudel = []
    sentences_strudel_timed = []
    sentence_chunks = []
    for sentence in sentence_word_phones:
        sentence_tokens = []
        for unit in sentence_chunk_plan(sentence):
            unit_type = unit[0]
            if unit_type == "oov":
                value = unit[1]
                sentence_tokens.append(safe_bank_name(value))
            else:
                chunk_key_raw = unit[3]
                chunk_key = safe_bank_name(chunk_key_raw, preserve_underscores=True)
                sentence_tokens.append(chunk_key)
                if not preview:
                    sentence_chunks.append(chunk_key)
        sentences_strudel.append(" ".join(sentence_tokens))
        sentences_strudel_timed.append(
            sentence_tokens_to_timed_lines(
                sentence_tokens,
                beats_per_bar=beats_per_bar,
                bars_per_line=bars_per_line,
                lead_in_beats=lead_in_beats,
                target_stress_beat=target_stress_beat,
            )
        )

    if strudel:
        reslist = {"_base": base}
    else:
        reslist = []

    if not preview:
        for word, phones in word_phones:
            if phones is None:
                # OOV: use whole-word sample
                bank = safe_bank_name(word)
                samples = dj.list(bank, gender=gender, language=language, soundtype="tts")
                for sound in samples:
                    if strudel:
                        if bank not in reslist:
                            reslist[bank] = []
                        reslist[bank].append(sound.file)
                    else:
                        reslist.append(
                            {
                                "url": sound.file,
                                "type": "audio",
                                "bank": bank,
                                "n": 0,
                                "oov": True,
                            }
                        )
                    break  # only one WAV per word/lang/gender

        seen_chunk_banks = set()
        for bank in sentence_chunks:
            if bank in seen_chunk_banks:
                continue
            seen_chunk_banks.add(bank)
            samples = dj.list(bank, gender=gender, language=language, soundtype="tts")
            for sound in samples:
                if strudel:
                    if bank not in reslist:
                        reslist[bank] = []
                    reslist[bank].append(sound.file)
                else:
                    reslist.append(
                        {
                            "url": sound.file,
                            "type": "audio",
                            "bank": bank,
                            "n": 0,
                            "oov": False,
                        }
                    )
                break  # only one WAV per chunk/lang/gender

    if strudel and details:
        reslist["sentences_strudel"] = sentences_strudel
        reslist["sentences_strudel_timed"] = sentences_strudel_timed
        reslist["sentences_phonetic"] = sentences_phonetic
        reslist["beats_per_bar"] = beats_per_bar
        reslist["bars_per_line"] = bars_per_line
        reslist["lead_in_beats"] = lead_in_beats
        reslist["target_stress_beat"] = target_stress_beat

    if not force:
        _phoneme_response_cache[response_cache_key] = reslist

    return jsonify(reslist)


@bp.route("/speech/<definition>.json")
async def speech_json(definition):
    """Download a reslist definition"""
    strudel = parse_bool_arg("strudel", False)
    gender = request.args.get("gender", "f")
    language = request.args.get("language", "en-GB")
    definition = definition.replace(" ", "_")

    await speech(definition)

    url = urlparse(request.base_url)
    scheme = url.scheme if url.hostname in ("localhost", "127.0.0.1") else "https"
    base = scheme + "://" + url.hostname
    if url.port:
        base += ":" + str(url.port)
    base += "/"
    try:
        words = dj.parse_definition(definition)
    except ValueError as ex:
        raise BadRequest(ex) from ex
    if strudel:
        reslist = {"_base": base}
    else:
        reslist = []
    for word in words:
        samples = dj.list(word, gender=gender, language=language, soundtype="tts")
        sample_num = 0
        for sound in samples:
            if strudel:
                if word not in reslist:
                    reslist[word] = []
                reslist[word].append(sound.file)
            else:
                sound_data = {
                    "url": sound.file,
                    "type": "audio",
                    "bank": word,
                    "n": sample_num,
                }
                reslist.append(sound_data)
                sample_num += 1

    return jsonify(reslist)


@bp.route("/speech_samples/<path:path>")
@bp.route("/speech/speech_samples/<path:path>")
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


@bp.route("/status")
def status():
    """Service availability status. Also triggers a lazy Freesound reconnect."""
    dj.try_reconnect()
    return jsonify(
        {
            "freesound": {
                "available": dj.freesound_available,
                "error": dj.freesound_error,
                "reason": dj.freesound_error_reason,
            },
            "speech": {"available": True},
        }
    )


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


async def speak_one(word, language, gender, force=False):
    """Speak a word"""
    return await dj.speak(word, language, gender, force=force)


async def speak_phoneme_one(arpabet_phone, ipa, language, gender, force=False):
    """Synthesise a single phoneme"""
    return await dj.speak_phoneme(arpabet_phone, ipa, language, gender, force=force)


async def speak_phoneme_chunk_one(
    chunk_key,
    ipa_phones,
    language,
    gender,
    text_hint="",
    force=False,
):
    """Synthesise a chunk of phonemes"""
    return await dj.speak_phoneme_chunk(
        chunk_key, ipa_phones, language, gender, text_hint=text_hint, force=force
    )


async def fetch_one(word, number, licenses):
    """Fetch a single sample set"""
    try:
        return await dj.fetch(word, number, licenses)
    except FreesoundUnavailableError as exc:
        return {"unavailable": True, "error": str(exc)}


def clean_definition(words):
    """reconstruct the definition without unwanted chars"""
    definition = []
    for word, number in words.items():
        definition.append(word + (":" + str(number) if number else ""))
    return ",".join(definition)
