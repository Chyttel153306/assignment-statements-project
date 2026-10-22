"""A total deterministic transition function over the tokenizer's finite alphabet."""
from dataclasses import dataclass
from core.tokenizer import Category as C, Token, to_dfa_tokens

INITIAL_STATE = "A"
ACCEPTING_STATES = frozenset({"H"})
DEAD_STATE = "DEAD"
STATE_DESCRIPTIONS = {
    "A": "Start: expect int followed by a space or tab",
    "B": "Expect the first identifier letter or underscore",
    "C": "Read identifier characters, then expect =",
    "D": "Expect the first integer digit",
    "E": "Read the first integer, then require an arithmetic operator",
    "F": "Expect an integer digit after the operator",
    "G": "Read subsequent integer digits, an operator, or a semicolon",
    "H": "Semicolon read: accept only when the input ends correctly",
    "DEAD": "Reject: no continuation can repair this prefix",
}
STATES = tuple(STATE_DESCRIPTIONS)
ALPHABET = (C.KEYWORD, C.LETTER, C.UNDERSCORE, C.DIGIT, C.ASSIGN,
            C.OPERATOR, C.SEMICOLON, C.SPACE, C.WORD_GAP, C.MISSING_SPACE,
            C.INVALID, C.EOF)

# This is the sole transition definition used by execution, table, and diagram.
TRANSITIONS = {(state, category): DEAD_STATE for state in STATES for category in ALPHABET}
for state in ("A", "B", "C", "D", "E", "F", "G", "H"):
    TRANSITIONS[state, C.SPACE] = state
TRANSITIONS.update({
    ("A", C.KEYWORD): "B",
    ("B", C.LETTER): "C",
    ("B", C.UNDERSCORE): "C",
    ("C", C.LETTER): "C",
    ("C", C.DIGIT): "C",
    ("C", C.UNDERSCORE): "C",
    ("C", C.ASSIGN): "D",
    ("D", C.DIGIT): "E",
    ("E", C.DIGIT): "E",
    ("E", C.OPERATOR): "F",
    ("F", C.DIGIT): "G",
    # Approved correction: later multi-digit operands stay distinct from E.
    ("G", C.DIGIT): "G",
    ("G", C.OPERATOR): "F",
    ("G", C.SEMICOLON): "H",
    ("H", C.EOF): "H",
})


def transition(state: str, category: C) -> str:
    return TRANSITIONS[state, category]


def grouped_transitions() -> dict[tuple[str, str], tuple[C, ...]]:
    """Group edges without duplicating the transition definitions."""
    groups: dict[tuple[str, str], list[C]] = {}
    for (previous, category), following in TRANSITIONS.items():
        groups.setdefault((previous, following), []).append(category)
    return {edge: tuple(categories) for edge, categories in groups.items()}


@dataclass(frozen=True)
class TraceStep:
    number: int
    token: Token
    previous: str
    following: str
    explanation: str

    @property
    def transition_label(self) -> str:
        return f"δ({self.previous}, {self.token.category.value}) → {self.following}"


@dataclass(frozen=True)
class DFAResult:
    accepted: bool
    final_state: str
    trace: tuple[TraceStep, ...]


def execute(tokens: list[Token]) -> DFAResult:
    """Execute character tokens from tokenize_for_dfa; retain the real path.

    H is accepting only after the explicit EOF token has been consumed. Merely
    reaching H on ';' in a truncated token stream does not accept the input.
    Original whole-lexeme streams are adapted for existing core callers.
    """
    if any(token.category in (C.IDENTIFIER, C.INTEGER, C.INVALID_IDENTIFIER) for token in tokens):
        tokens = to_dfa_tokens(tokens)
    state = INITIAL_STATE
    trace = []
    for number, token in enumerate(tokens, 1):
        following = transition(state, token.category)
        explanation = (f"Unexpected {token.category.value}. {STATE_DESCRIPTIONS[state]}."
                       if following == DEAD_STATE else STATE_DESCRIPTIONS[following] + ".")
        trace.append(TraceStep(number, token, state, following, explanation))
        state = following
        if state == DEAD_STATE:
            break
    ended = bool(tokens) and tokens[-1].category == C.EOF
    return DFAResult(state in ACCEPTING_STATES and ended, state, tuple(trace))
