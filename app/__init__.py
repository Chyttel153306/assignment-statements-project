"""Local Flask interface around the preserved DFA core."""
import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from core.validator import validate
from app.presentation import dfa_definition, serialize_result

ROOT = Path(__file__).resolve().parent.parent
MAX_STATEMENT_LENGTH = 20000


def load_test_cases():
    return json.loads((ROOT / "data" / "test_cases.json").read_text(encoding="utf-8"))


def create_app(test_config=None):
    app = Flask(__name__, template_folder=str(ROOT / "templates"), static_folder=str(ROOT / "static"))
    app.config.update(MAX_CONTENT_LENGTH=128 * 1024, JSON_SORT_KEYS=False)
    if test_config:
        app.config.update(test_config)

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", service="Assignment Statement DFA Validator")

    @app.get("/api/dfa")
    def dfa():
        return jsonify(dfa_definition())

    @app.get("/api/examples")
    def examples():
        return jsonify(cases=[dict(case, id=index) for index, case in enumerate(load_test_cases())])

    @app.post("/api/validate")
    def validate_statement():
        if not request.is_json:
            return jsonify(error="Send a JSON object with a 'statement' text field."), 415
        payload = request.get_json()
        if not isinstance(payload, dict) or "statement" not in payload:
            return jsonify(error="Include a 'statement' text field in your request."), 400
        source = payload["statement"]
        if not isinstance(source, str):
            return jsonify(error="The statement must be text."), 400
        if len(source) > MAX_STATEMENT_LENGTH:
            return jsonify(error=f"Please use at most {MAX_STATEMENT_LENGTH:,} characters per statement."), 413
        return jsonify(serialize_result(validate(source)))

    @app.post("/api/test-cases/run")
    def run_tests():
        results = []
        for index, case in enumerate(load_test_cases()):
            result = serialize_result(validate(case["source"]))
            results.append(dict(case, id=index, actual=result["accepted"],
                                passed=result["accepted"] == case["expected"], message=result["message"]))
        passed = sum(case["passed"] for case in results)
        return jsonify(cases=results, total=len(results), passed=passed, failed=len(results)-passed)

    @app.errorhandler(Exception)
    def handle_error(error):
        if isinstance(error, HTTPException):
            messages = {400: "We couldn't read that JSON request. Please check its format.",
                        404: "That address was not found.", 405: "That action is not supported at this address.",
                        413: "That request is too large. Try a shorter statement."}
            return jsonify(error=messages.get(error.code, "The request could not be completed.")), error.code
        app.logger.exception("Unexpected request failure")
        return jsonify(error="Something went wrong while checking your request. Please try again."), 500

    return app
