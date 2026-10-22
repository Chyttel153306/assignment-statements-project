"""Public validation service shared by the Flask API and automated tests."""
from dataclasses import dataclass
from core.tokenizer import Category as C, Token, tokenize, to_dfa_tokens
from core.dfa_engine import DFAResult, execute
from core.semantic_checker import check_semantics


@dataclass(frozen=True)
class ValidationResult:
    source: str
    accepted: bool
    syntax_accepted: bool
    message: str
    error_start: int | None
    error_end: int | None
    error_token_index: int | None
    tokens: tuple[Token, ...]
    dfa: DFAResult


def syntax_error(source: str, dfa: DFAResult) -> str:
    step = dfa.trace[-1]
    token, state = step.token, step.previous
    if not source.strip(" \t"):
        return "Empty input. Enter an assignment such as int a = 8 + 8;"
    if state == "A":
        if token.category == C.MISSING_SPACE:
            return "Missing whitespace after 'int'. Separate the keyword and identifier with a space or tab."
        if token.text.startswith("int") and token.text != "int":
            return "Missing whitespace after 'int'. Separate the keyword and identifier with a space or tab."
        return "Missing 'int' keyword. The statement must begin with the exact lowercase keyword int."
    if token.category == C.WORD_GAP:
        return ("Whitespace cannot split an identifier. Expected the assignment operator '=' after the identifier."
                if state == "C" else "Whitespace cannot split an integer literal. Put an operator between separate numbers.")
    if token.category == C.INVALID:
        return f"Invalid character {token.text!r}. Only ASCII names, integers, =, +, -, *, /, spaces, tabs, and ; are supported."
    if state == "B":
        return "Invalid or missing identifier. Start with an ASCII letter or underscore, followed by letters, digits, or underscores."
    if state == "C":
        return "Missing assignment operator. Expected a single '=' after the identifier."
    if state == "D":
        if token.category == C.ASSIGN:
            return "Unexpected '='. Use a single assignment operator; '==' is unsupported."
        return "Missing first operand. Expected an unsigned integer; variables and unary signs are unsupported."
    if state == "E":
        return "Missing arithmetic operator. At least one +, -, *, or / operation is required."
    if state == "F":
        return "Missing operand after an operator. Expected an unsigned integer; repeated operators are unsupported."
    if state == "G":
        return ("Missing semicolon at the end of the assignment." if token.category == C.EOF
                else "Expected an arithmetic operator or the terminating semicolon.")
    if state == "H":
        return ("Unexpected extra semicolon. Only one assignment is allowed." if token.category == C.SEMICOLON
                else "Unexpected content after the semicolon. Only one assignment is allowed.")
    return "Input does not follow the assignment grammar."


def validate(source: str) -> ValidationResult:
    lexemes = tokenize(source)
    tokens = to_dfa_tokens(lexemes)
    dfa = execute(tokens)
    if not dfa.accepted:
        step = dfa.trace[-1]
        error_start = step.token.end if step.token.category == C.MISSING_SPACE else step.token.start
        return ValidationResult(source, False, False, syntax_error(source, dfa), error_start,
                                step.token.end, step.number, tuple(tokens), dfa)
    issue = check_semantics(lexemes)
    if issue:
        index = next(i for i, token in enumerate(tokens, 1) if token.start == issue.token.start)
        return ValidationResult(source, False, True, issue.message, issue.token.start, issue.token.end,
                                index, tuple(tokens), dfa)
    return ValidationResult(source, True, True,
                            "The DFA accepted the complete statement. No literal division by zero was found.",
                            None, None, None, tuple(tokens), dfa)
