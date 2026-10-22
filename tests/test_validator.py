import json
from pathlib import Path
import random
import unittest
from core.validator import validate
from core.tokenizer import Category


class ValidatorTests(unittest.TestCase):
    def test_all_laboratory_expectations(self):
        path = Path(__file__).resolve().parent.parent / "data" / "test_cases.json"
        for case in json.loads(path.read_text(encoding="utf-8")):
            with self.subTest(source=case["source"], purpose=case["purpose"]):
                self.assertEqual(validate(case["source"]).accepted, case["expected"])

    def test_separate_syntax_and_semantics(self):
        result = validate("int a=8/00;")
        self.assertFalse(result.accepted)
        self.assertTrue(result.syntax_accepted)
        self.assertEqual(result.dfa.final_state, "H")
        self.assertEqual(result.error_start, 8)
        self.assertEqual(result.tokens[result.error_token_index-1].text, "0")
        self.assertEqual(result.source[result.error_start:result.error_end], "00")

    def test_syntax_errors_take_priority(self):
        result = validate("int a=8/0")
        self.assertFalse(result.syntax_accepted)
        self.assertIn("semicolon", result.message)

    def test_helpful_messages(self):
        cases = [("", "Empty"), ("inta=1+2;", "whitespace"), ("int=1+2;", "whitespace"),
                 ("float a=1+2;", "keyword"), ("int 1a=1+2;", "identifier"),
                 ("int a 1+2;", "assignment"), ("int a=;", "first operand"),
                 ("int a=1;", "arithmetic operator"), ("int a=1++2;", "operand after"),
                 ("int a=1+2", "semicolon"), ("int a=1+2;;", "extra semicolon"),
                 ("int a=1.0+2;", "Invalid character"), ("int a==1+2;", "single assignment")]
        for source, fragment in cases:
            with self.subTest(source=source):
                result = validate(source)
                self.assertFalse(result.accepted)
                self.assertIn(fragment, result.message)
                self.assertIsNotNone(result.error_start)

    def test_error_span_and_eof_location(self):
        source = "int a=1++2;"
        result = validate(source)
        self.assertEqual(source[result.error_start:result.error_end], "+")
        result = validate("int a=1+2")
        self.assertEqual(result.error_start, len(result.source))
        self.assertEqual(result.tokens[result.error_token_index-1].category, Category.EOF)

    def test_long_integers_do_not_use_numeric_conversion(self):
        self.assertTrue(validate("int a="+"9"*10000+"/"+"0"*10000+"5;").accepted)

    def test_generated_valid_assignments_and_invalid_mutations(self):
        rng = random.Random(2026)
        for _ in range(200):
            name = rng.choice(("a", "_x1", "Sum_99", "__"))
            operands = [str(rng.randint(1, 9999)) for _ in range(rng.randint(2, 8))]
            expression = operands[0]
            for operand in operands[1:]:
                expression += rng.choice(("", " ", "\t")) + rng.choice("+-*/") + rng.choice(("", " ", "\t")) + operand
            source = f"int {name}={expression};"
            with self.subTest(source=source):
                self.assertTrue(validate(source).accepted)
                self.assertFalse(validate(source[:-1]).accepted)
                self.assertFalse(validate(source+";").accepted)
                self.assertFalse(validate(source.replace("=", "==", 1)).accepted)


if __name__ == "__main__":
    unittest.main()
