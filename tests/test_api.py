"""Exercise the real Flask API and verify its graph/trace contract."""
import unittest
from unittest.mock import patch

from app import create_app, load_test_cases
from core.dfa_engine import TRANSITIONS, INITIAL_STATE, ACCEPTING_STATES
from core.tokenizer import Category
from core.validator import validate


class APITests(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True})
        self.client = self.app.test_client()

    def check(self, source):
        response = self.client.post("/api/validate", json={"statement": source})
        self.assertEqual(response.status_code, 200)
        return response.get_json()

    def test_health_and_frontend_assets(self):
        self.assertEqual(self.client.get("/api/health").get_json()["status"], "ok")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Assignment Statement Validator', response.data)
        self.assertNotIn(b'https://', response.data)
        for path in ("/static/css/style.css", "/static/js/app.js", "/static/js/dfa_visualizer.js", "/static/assets/favicon.svg"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                response.close()

    def test_graph_is_the_complete_runtime_dfa(self):
        graph = self.client.get("/api/dfa").get_json()
        self.assertEqual(graph["initial_state"], INITIAL_STATE)
        self.assertEqual(set(graph["accepting_states"]), ACCEPTING_STATES)
        transitions = {(e["from"], Category(e["symbol"])): e["to"] for e in graph["transitions"]}
        groups = {(e["from"], Category(symbol)): e["to"] for e in graph["edges"] for symbol in e["symbols"]}
        self.assertEqual(transitions, TRANSITIONS)
        self.assertEqual(groups, TRANSITIONS)
        self.assertEqual({s["id"] for s in graph["states"]}, {state for state, _ in TRANSITIONS})

    def test_trace_state_path_and_diagram_agree_for_every_case(self):
        for case in load_test_cases():
            with self.subTest(source=case["source"]):
                result = self.check(case["source"])
                original = validate(case["source"])
                self.assertEqual(result["input"], case["source"])
                self.assertEqual(result["accepted"], case["expected"])
                self.assertEqual(result["syntax_accepted"], original.syntax_accepted)
                self.assertEqual(result["state_path"], [INITIAL_STATE]+[s.following for s in original.dfa.trace])
                self.assertEqual(result["diagram"]["current_state"], result["final_state"])
                for step, edge, previous, following in zip(result["trace"], result["diagram"]["transitions"], result["state_path"], result["state_path"][1:]):
                    self.assertEqual(step["previous_state"], previous)
                    self.assertEqual(step["next_state"], following)
                    self.assertEqual(TRANSITIONS[previous, Category(step["category"])], following)
                    self.assertEqual(edge, {"from": previous, "symbol": step["symbol"], "to": following})
                self.assertEqual(len(result["trace"])+1, len(result["state_path"]))

    def test_semantic_rejection_keeps_accepting_syntax_path(self):
        result = self.check("int a=8/00;")
        self.assertFalse(result["accepted"])
        self.assertTrue(result["syntax_accepted"])
        self.assertFalse(result["semantic_accepted"])
        self.assertEqual(result["error"]["type"], "semantic")
        self.assertEqual(result["error"]["start"], 8)
        self.assertEqual(result["error"]["character"], 9)
        self.assertEqual(result["final_state"], "H")

    def test_friendly_errors_and_no_semantics_after_syntax_failure(self):
        for source, phrase in (("int a=5+;", "after the '+'"), ("int a=5+5", "end with a semicolon"),
                               ("", "Enter an assignment"), ("int a=8/0", "semicolon")):
            with self.subTest(source=source):
                result = self.check(source)
                self.assertIn(phrase, result["message"])
                self.assertEqual(result["error"]["type"], "syntax")
                self.assertIsNone(result["semantic_accepted"])

    def test_json_request_validation(self):
        for payload in ({}, [], None, "int a=1+2;", {"statement": None}, {"statement": 12}, {"statement": []}, {"statement": False}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/validate", data=__import__('json').dumps(payload), content_type="application/json")
                self.assertEqual(response.status_code, 400)
                self.assertIn("error", response.get_json())

    def test_malformed_json_and_wrong_content_type(self):
        for raw in ("{", '{"statement":', ""):
            response = self.client.post("/api/validate", data=raw, content_type="application/json")
            self.assertEqual(response.status_code, 400)
            self.assertIn("error", response.get_json())
        self.assertEqual(self.client.post("/api/validate", data="hello").status_code, 415)

    def test_request_limits(self):
        self.assertEqual(self.client.post("/api/validate", json={"statement": "x"*20001}).status_code, 413)
        self.assertEqual(self.client.post("/api/validate", data="x"*140000, content_type="application/json").status_code, 413)

    def test_examples_and_laboratory_are_real_runs(self):
        examples = self.client.get("/api/examples").get_json()["cases"]
        response = self.client.post("/api/test-cases/run").get_json()
        self.assertEqual(len(examples), len(load_test_cases()))
        self.assertEqual(response["total"], len(examples))
        self.assertEqual(response["failed"], 0)
        for case in response["cases"]:
            self.assertEqual(case["actual"], validate(case["source"]).accepted)
            self.assertEqual(case["passed"], case["actual"] == case["expected"])

    def test_unknown_routes_and_wrong_methods_are_json(self):
        self.assertEqual(self.client.get("/missing").status_code, 404)
        self.assertIn("error", self.client.get("/missing").get_json())
        self.assertEqual(self.client.get("/api/validate").status_code, 405)

    def test_unexpected_errors_do_not_expose_internal_details(self):
        with patch("app.validate", side_effect=RuntimeError("private internal details")), self.assertLogs(self.app.logger, level="ERROR"):
            response = self.client.post("/api/validate", json={"statement": "int a=1+2;"})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("private", response.get_data(as_text=True))
        self.assertNotIn("Traceback", response.get_data(as_text=True))

    def test_input_is_returned_as_data_not_executed(self):
        source = '<script>alert("hello")</script>'
        result = self.check(source)
        self.assertEqual(result["input"], source)
        self.assertFalse(result["accepted"])


if __name__ == "__main__":
    unittest.main()
