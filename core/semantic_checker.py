"""Semantic checks for a syntactically accepted token stream. No evaluation."""
from dataclasses import dataclass
from core.tokenizer import Category, Token


@dataclass(frozen=True)
class SemanticIssue:
    message: str
    token: Token


def check_semantics(tokens: list[Token]) -> SemanticIssue | None:
    """Detect literal zero divisors, including arbitrarily long zero strings."""
    meaningful = [t for t in tokens if t.category != Category.SPACE]
    for previous, token in zip(meaningful, meaningful[1:]):
        if previous.text == "/" and token.category == Category.INTEGER and all(c == "0" for c in token.text):
            return SemanticIssue("Division by zero: the integer immediately after '/' contains only zeros.", token)
    return None
