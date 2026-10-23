"""Verify the teaching sections describe and run the actual assignment language."""
from html.parser import HTMLParser
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

from app import create_app, load_test_cases
from app.presentation import SYNTAX_REGEX
from core.validator import validate

ROOT = Path(__file__).resolve().parent.parent


class TeachingContent(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.headings = []
        self.codes = {}
        self.heading = False
        self.code_id = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == "h2":
            self.heading = True
        if tag == "code":
            self.code_id = dict(attrs).get("id")
            if self.code_id:
                self.codes[self.code_id] = ""

    def handle_endtag(self, tag):
        if tag == "h2":
            self.heading = False
        if tag == "code":
            self.code_id = None

    def handle_data(self, data):
        if self.heading:
            self.headings.append(data)
        if self.code_id:
            self.codes[self.code_id] += data


class TeachingTests(unittest.TestCase):
    def test_all_four_teaching_sections_and_exact_program_are_served(self):
        response = create_app({"TESTING": True}).test_client().get("/")
        self.assertEqual(response.status_code, 200)
        page = TeachingContent(response.get_data(as_text=True))
        for heading in ("Regular Expression", "Deterministic Finite Automaton (DFA)",
                        "Transition Diagram", "Short Python Program"):
            self.assertIn(heading, page.headings)
        self.assertEqual(page.codes["syntax-regex"], SYNTAX_REGEX)
        self.assertEqual(page.codes["python-program"],
                         (ROOT / "tools" / "recognize_assignment.py").read_text(encoding="utf-8"))

    def test_displayed_regex_matches_actual_syntax_including_zero_division(self):
        for case in load_test_cases():
            with self.subTest(source=case["source"]):
                self.assertEqual(re.fullmatch(SYNTAX_REGEX, case["source"]) is not None,
                                 validate(case["source"]).syntax_accepted)
        self.assertIsNotNone(re.fullmatch(SYNTAX_REGEX, "int a=8/00;"))
        self.assertFalse(validate("int a=8/00;").accepted)

    def test_runnable_program_for_valid_syntax_invalid_and_semantic_invalid_input(self):
        for source in ("int a = 8 + 8;", "int a=x+1;", "int a=1+x;", "int a=8/00;"):
            with self.subTest(source=source):
                result = validate(source)
                process = subprocess.run(
                    [sys.executable, "-m", "tools.recognize_assignment", source], cwd=ROOT,
                    capture_output=True, text=True, encoding="utf-8", timeout=10,
                    env=dict(os.environ, PYTHONIOENCODING="utf-8"))
                self.assertEqual(process.returncode, 0 if result.accepted else 1, process.stderr)
                self.assertIn(("VALID" if result.accepted else "INVALID") + ": " + result.message,
                              process.stdout)
                self.assertIn("--> " + result.dfa.final_state, process.stdout)

    def test_runnable_program_prompts_when_no_argument_is_supplied(self):
        process = subprocess.run([sys.executable, "-m", "tools.recognize_assignment"], cwd=ROOT,
                                 input="int a=1+2;\n", capture_output=True, text=True,
                                 encoding="utf-8", timeout=10,
                                 env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("Assignment: VALID:", process.stdout)


if __name__ == "__main__":
    unittest.main()
