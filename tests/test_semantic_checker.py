import unittest
from core.tokenizer import tokenize
from core.semantic_checker import check_semantics


class SemanticTests(unittest.TestCase):
    def test_zero_divisors(self):
        for value in ("0", "00", "00000", "0"*10000):
            with self.subTest(length=len(value)):
                issue = check_semantics(tokenize(f"int a=8 / \t{value};"))
                self.assertIsNotNone(issue)
                self.assertEqual(issue.token.text, value)

    def test_nonzero_divisors(self):
        for value in ("05", "0001", "10", "9"*10000):
            with self.subTest(length=len(value)):
                self.assertIsNone(check_semantics(tokenize(f"int a=8/{value};")))

    def test_zero_in_other_positions(self):
        self.assertIsNone(check_semantics(tokenize("int a=0+0-0*0;")))

    def test_later_zero_divisor_location(self):
        source = "int a=1+2/000;"
        issue = check_semantics(tokenize(source))
        self.assertEqual(issue.token.start, source.index("000"))


if __name__ == "__main__":
    unittest.main()
