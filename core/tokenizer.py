"""Lossless tokenizer with zero-based character spans and an explicit EOF token."""
from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    KEYWORD = "INT"
    SPACE = "SPACE"
    IDENTIFIER = "IDENTIFIER"
    INTEGER = "INTEGER"
    ASSIGN = "="
    OPERATOR = "OPERATOR"
    SEMICOLON = ";"
    INVALID_IDENTIFIER = "INVALID_IDENTIFIER"
    INVALID = "INVALID"
    EOF = "EOF"
    LETTER = "LETTER"
    DIGIT = "DIGIT"
    UNDERSCORE = "UNDERSCORE"
    WORD_GAP = "WORD_GAP"
    MISSING_SPACE = "MISSING_SPACE"


@dataclass(frozen=True)
class Token:
    text: str
    category: Category
    start: int
    end: int

    @property
    def display(self) -> str:
        if self.category == Category.EOF:
            return "<end>"
        if self.category in (Category.SPACE, Category.WORD_GAP, Category.KEYWORD):
            return self.text.replace(" ", "·").replace("\t", "\\t")
        return self.text.replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")


def is_letter(char: str) -> bool:
    return "a" <= char <= "z" or "A" <= char <= "Z"


def is_digit(char: str) -> bool:
    return "0" <= char <= "9"


def tokenize(source: str) -> list[Token]:
    """Recognize ASCII identifiers, unsigned integers, spaces/tabs, and punctuation.

    Runs such as 12name are one invalid identifier, preventing accidental splitting.
    No token is discarded, so required keyword whitespace remains visible to the DFA.
    """
    tokens: list[Token] = []
    index = 0
    punctuation = {"=": Category.ASSIGN, ";": Category.SEMICOLON}
    while index < len(source):
        start = index
        char = source[index]
        if char in " \t":
            index += 1
            while index < len(source) and source[index] in " \t":
                index += 1
            category = Category.SPACE
        elif is_letter(char) or is_digit(char) or char == "_":
            index += 1
            while index < len(source) and (is_letter(source[index]) or is_digit(source[index]) or source[index] == "_"):
                index += 1
            word = source[start:index]
            if word == "int":
                category = Category.KEYWORD
            elif all(is_digit(c) for c in word):
                category = Category.INTEGER
            elif is_digit(word[0]):
                category = Category.INVALID_IDENTIFIER
            else:
                category = Category.IDENTIFIER
        else:
            index += 1
            category = Category.OPERATOR if char in "+-*/" else punctuation.get(char, Category.INVALID)
        tokens.append(Token(source[start:index], category, start, index))
    tokens.append(Token("", Category.EOF, len(source), len(source)))
    return tokens


def to_dfa_tokens(tokens: list[Token]) -> list[Token]:
    """Adapt lexemes to the A–H character DFA without losing source spans.

    INT is the lexical unit 'int' plus its mandatory space/tab separator.
    A missing separator is a lexical error class, never a valid INT unit.
    Names/numbers are expanded into actual characters. WORD_GAP marks whitespace
    between word lexemes, so the DFA cannot join 'ab cd' or '12 34' by ignoring
    spaces. Other spaces remain SPACE tokens. This lexer does not decide whether
    an assignment is accepted; every emitted category is processed by the DFA.
    """
    result: list[Token] = []
    first_word = True
    word_classes = {Category.KEYWORD, Category.IDENTIFIER, Category.INTEGER,
                    Category.INVALID_IDENTIFIER}
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if first_word and token.category not in (Category.SPACE, Category.EOF):
            first_word = False
            if token.category == Category.KEYWORD:
                if index + 1 < len(tokens) and tokens[index + 1].category == Category.SPACE:
                    separator = tokens[index + 1]
                    result.append(Token(token.text + separator.text, Category.KEYWORD, token.start, separator.end))
                    index += 2
                    continue
                result.append(Token(token.text, Category.MISSING_SPACE, token.start, token.end))
            else:
                result.append(Token(token.text, Category.INVALID, token.start, token.end))
        elif token.category in word_classes:
            for offset, char in enumerate(token.text):
                category = Category.LETTER if is_letter(char) else Category.DIGIT if is_digit(char) else Category.UNDERSCORE
                result.append(Token(char, category, token.start + offset, token.start + offset + 1))
        elif token.category == Category.SPACE:
            between_words = (index > 0 and index + 1 < len(tokens)
                             and tokens[index - 1].category in word_classes
                             and tokens[index + 1].category in word_classes)
            result.append(Token(token.text, Category.WORD_GAP if between_words else Category.SPACE, token.start, token.end))
        else:
            result.append(token)
        index += 1
    return result


def tokenize_for_dfa(source: str) -> list[Token]:
    """Public source-to-character-token adapter for DFA execution."""
    return to_dfa_tokens(tokenize(source))
