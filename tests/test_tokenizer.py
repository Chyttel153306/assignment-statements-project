import unittest
from core.tokenizer import Category as C, tokenize


class TokenizerTests(unittest.TestCase):
    def test_lossless_tokens_and_spans(self):
        source = " \tint abc_2=001+2; "
        tokens = tokenize(source)
        self.assertEqual("".join(t.text for t in tokens), source)
        for token in tokens:
            self.assertEqual(source[token.start:token.end], token.text)
        self.assertEqual(tokens[-1].category, C.EOF)
        self.assertEqual(tokens[-1].start, len(source))

    def test_categories(self):
        self.assertEqual([t.category for t in tokenize("int\ta=1+2;")],
                         [C.KEYWORD, C.SPACE, C.IDENTIFIER, C.ASSIGN, C.INTEGER,
                          C.OPERATOR, C.INTEGER, C.SEMICOLON, C.EOF])

    def test_identifier_classes(self):
        for text in ("a", "_", "X_9", "abc123", "__"):
            with self.subTest(text=text):
                self.assertEqual(tokenize(text)[0].category, C.IDENTIFIER)
        for text in ("1a", "9_", "123abc"):
            with self.subTest(text=text):
                self.assertEqual(tokenize(text)[0].category, C.INVALID_IDENTIFIER)

    def test_unsupported_characters_are_retained(self):
        for text in ("@", "é", "２", "\n", "\r", "\u00a0", ".", "("):
            with self.subTest(text=repr(text)):
                self.assertEqual(tokenize(text)[0].category, C.INVALID)

    def test_equality_is_two_assign_tokens(self):
        self.assertEqual([t.category for t in tokenize("==")], [C.ASSIGN, C.ASSIGN, C.EOF])

    def test_whitespace_display_is_visible(self):
        self.assertEqual(tokenize(" \t ")[0].display, "·\\t·")


if __name__ == "__main__":
    unittest.main()
