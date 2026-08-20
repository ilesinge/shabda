"""Tests for sentence chunk planning."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_web_module():
    package_root = Path(__file__).resolve().parents[1]

    flask = types.ModuleType("flask")

    class Blueprint:
        def __init__(self, *args, **kwargs):
            pass

        def route(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    flask.Blueprint = Blueprint
    flask.jsonify = lambda *args, **kwargs: None
    flask.send_from_directory = lambda *args, **kwargs: None
    flask.request = types.SimpleNamespace(args={})
    flask.render_template = lambda *args, **kwargs: ""
    flask.send_file = lambda *args, **kwargs: None
    flask.after_this_request = lambda func: func
    sys.modules["flask"] = flask

    werkzeug = types.ModuleType("werkzeug")
    exceptions = types.ModuleType("werkzeug.exceptions")

    class BadRequest(Exception):
        pass

    class HTTPException(Exception):
        pass

    exceptions.BadRequest = BadRequest
    exceptions.HTTPException = HTTPException
    werkzeug.exceptions = exceptions
    sys.modules["werkzeug"] = werkzeug
    sys.modules["werkzeug.exceptions"] = exceptions

    shabda_pkg = types.ModuleType("shabda")
    shabda_pkg.__path__ = [str(package_root / "shabda")]
    sys.modules["shabda"] = shabda_pkg

    dj_module = types.ModuleType("shabda.dj")

    class Dj:
        def __init__(self, *args, **kwargs):
            pass

    dj_module.Dj = Dj
    sys.modules["shabda.dj"] = dj_module

    client_module = types.ModuleType("shabda.client")

    class FreesoundUnavailableError(Exception):
        pass

    client_module.FreesoundUnavailableError = FreesoundUnavailableError
    sys.modules["shabda.client"] = client_module

    web_path = package_root / "shabda" / "web.py"
    spec = importlib.util.spec_from_file_location("shabda.web", web_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["shabda.web"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_sentence_chunk_plan_keeps_each_word_isolated():
    web = _load_web_module()

    plan = web.sentence_chunk_plan(
        [
            ("hello", ["HH", "AH0", "L", "OW1"]),
            ("a", ["AH0"]),
        ]
    )

    assert plan == [
        ("chunk", ["HH", "AH0"], "hello", "phc_HH_AH0"),
        ("chunk", ["L", "OW1"], "hello", "phc_L_OW1"),
        ("chunk", ["AH0"], "a", "phc_AH0"),
    ]