"""Contract from the reference document's final assignment test-case table.

The user confirmed this table governs recognition. The earlier plain-assignment
rules and password DFA in that document describe different languages.
"""
import unittest

from app import create_app, load_test_cases
from core.validator import validate


# Keep the document's exact spelling and spacing, including its boundary cases.
# Third field is expected syntax acceptance; zero division fails semantics only.
DOCUMENT_CASES = (
    ("int a = 8 + 8;", True, True),
    ("int a=3+4+4;", True, True),
    ("int sum = 1+2+3-8*2/8;", True, True),
    ("int x_1 = 10 / 5;", True, True),
    ("int a = 8/05;", True, True),
    ("int a = -5;", False, False),
    ("int a = 8/0;", False, True),
    ("int a = 8 / 00;", False, True),
    ("int a = 8;", False, False),
    ("inta = 5+5;", False, False),
    ("int 1a = 5+5;", False, False),
    ("int a = 5++5;", False, False),
    ("int a = 5+;", False, False),
    ("int a = 5+5", False, False),
    ("int a = 5+5;;", False, False),
    ("int a = x + 1;", False, False),
)


class DocumentationTests(unittest.TestCase):
    def test_document_examples_through_core_and_api(self):
        client = create_app({"TESTING": True}).test_client()
        for source, accepted, syntax in DOCUMENT_CASES:
            with self.subTest(source=source):
                result = validate(source)
                self.assertEqual(result.accepted, accepted)
                self.assertEqual(result.syntax_accepted, syntax)
                response = client.post("/api/validate", json={"statement": source})
                self.assertEqual(response.status_code, 200)
                payload = response.get_json()
                self.assertEqual(payload["accepted"], accepted)
                self.assertEqual(payload["syntax_accepted"], syntax)
                self.assertEqual(payload["semantic_accepted"], accepted if syntax else None)
                self.assertEqual(payload["final_state"], "H" if syntax else "DEAD")
                if not accepted:
                    self.assertEqual(payload["error"]["type"], "semantic" if syntax else "syntax")

    def test_all_document_examples_are_available_in_the_laboratory(self):
        cases = {case["source"]: case["expected"] for case in load_test_cases()}
        for source, accepted, _ in DOCUMENT_CASES:
            with self.subTest(source=source):
                self.assertIn(source, cases)
                self.assertEqual(cases[source], accepted)

    def test_confirmed_language_excludes_the_conflicting_document_sections(self):
        for source in ("x = 10;", "total = a + b;", "sum1 = 25 * 2;", "ab@123"):
            with self.subTest(source=source):
                self.assertFalse(validate(source).accepted)


if __name__ == "__main__":
    unittest.main()
