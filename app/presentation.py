"""JSON presentation adapters. Recognition remains exclusively in core/."""
from core.dfa_engine import (STATES, ALPHABET, TRANSITIONS, INITIAL_STATE,
                             ACCEPTING_STATES, DEAD_STATE, STATE_DESCRIPTIONS, grouped_transitions)
from core.tokenizer import Category as C

SYNTAX_REGEX = r"[ \t]*int[ \t]+[A-Za-z_][A-Za-z_0-9]*[ \t]*=[ \t]*[0-9]+(?:[ \t]*[+*/-][ \t]*[0-9]+)+[ \t]*;[ \t]*"


def dfa_definition():
    return {
        "states": [{"id": state, "description": STATE_DESCRIPTIONS[state],
                    "accepting": state in ACCEPTING_STATES, "dead": state == DEAD_STATE} for state in STATES],
        "alphabet": [category.value for category in ALPHABET],
        "initial_state": INITIAL_STATE, "accepting_states": sorted(ACCEPTING_STATES), "dead_state": DEAD_STATE,
        "transitions": [{"from": previous, "symbol": category.value, "to": following}
                        for (previous, category), following in TRANSITIONS.items()],
        "edges": [{"from": previous, "to": following, "symbols": [c.value for c in categories]}
                  for (previous, following), categories in grouped_transitions().items()],
    }


def friendly_message(result):
    if result.accepted:
        return "Your assignment statement follows the supported syntax."
    if result.syntax_accepted:
        return "Division by zero is not allowed. Check the number after '/'."
    step = result.dfa.trace[-1]
    state, token = step.previous, step.token
    if not result.source.strip(" \t"):
        return "Enter an assignment statement first, such as int total = 8 + 5;"
    if state == "A":
        return ("Add a space or tab between 'int' and the variable name." if token.category == C.MISSING_SPACE or token.text.startswith("int") and token.text != "int"
                else "Start your statement with the lowercase keyword 'int'.")
    if token.category == C.WORD_GAP:
        return ("Do not put spaces inside a variable name. Put '=' after the complete name."
                if state == "C" else "Do not put spaces inside a number. Put an operator between separate numbers.")
    if token.category == C.INVALID:
        return f"The character {token.display!r} is not supported. Use whole numbers, names, and the allowed symbols."
    if state == "B":
        return "Add a valid variable name. Start with a letter or underscore, then use letters, numbers, or underscores."
    if state == "C":
        return "Add an equals sign (=) after the variable name."
    if state == "D":
        return ("Use one equals sign (=), rather than two (==)." if token.category == C.ASSIGN
                else "Add the first whole number after '='. Variable names and signed numbers are not allowed here.")
    if state == "E":
        return "Include at least one arithmetic operation, such as 8 + 5. Use +, -, *, or /."
    if state == "F":
        operator = next((s.token.text for s in reversed(result.dfa.trace[:-1]) if s.token.category == C.OPERATOR), "")
        return f"Your statement is missing a number after the '{operator}' operator."
    if state == "G":
        return ("Your statement must end with a semicolon (;)." if token.category == C.EOF
                else "Put an arithmetic operator or a semicolon (;) after this number.")
    if state == "H":
        return ("Use just one semicolon (;) at the end." if token.category == C.SEMICOLON
                else "Remove the extra content after the semicolon (;). Check one statement at a time.")
    return result.message


def step_explanation(step):
    token = step.token
    if step.following == DEAD_STATE:
        return f"This token is not allowed here. {STATE_DESCRIPTIONS[step.previous]}. The DFA moves to DEAD."
    if token.category == C.SPACE:
        return "The DFA reads optional spaces or tabs and stays in the same state."
    descriptions = {C.EOF: "The input is complete. The DFA accepts its syntax.",
                    C.KEYWORD: "The DFA reads 'int' with its required space or tab and moves to B.",
                    C.DIGIT: f"The DFA reads the digit '{token.text}' and moves to {step.following}.",
                    C.OPERATOR: f"The DFA reads '{token.text}'. A whole number must follow.",
                    C.ASSIGN: "The DFA reads '='. The expression starts next.",
                    C.SEMICOLON: "The DFA reads ';'. Only spaces, tabs, and the end of input may follow."}
    if token.category in (C.LETTER, C.UNDERSCORE):
        return (f"The variable name starts with '{token.text}'. The DFA moves to C." if step.previous == "B"
                else f"The DFA reads '{token.text}' as another character in the variable name and stays in C.")
    if token.category == C.DIGIT and step.previous == "C":
        return f"The DFA reads '{token.text}' as another character in the variable name and stays in C."
    return descriptions.get(token.category, step.explanation)


def serialize_result(result):
    trace = [{"step": s.number, "token": s.token.text, "display": s.token.display,
              "category": s.token.category.value, "start": s.token.start, "end": s.token.end,
              "previous_state": s.previous, "next_state": s.following,
              "symbol": s.token.category.value, "transition": s.transition_label,
              "explanation": step_explanation(s)} for s in result.dfa.trace]
    error = None if result.accepted else {"type": "semantic" if result.syntax_accepted else "syntax",
        "message": friendly_message(result), "start": result.error_start, "end": result.error_end,
        "character": result.error_start + 1, "token_index": result.error_token_index}
    return {"input": result.source, "accepted": result.accepted, "syntax_accepted": result.syntax_accepted,
            "semantic_accepted": result.accepted if result.syntax_accepted else None,
            "message": friendly_message(result), "error": error, "final_state": result.dfa.final_state,
            "trace": trace, "state_path": [INITIAL_STATE] + [step.following for step in result.dfa.trace],
            "diagram": {"current_state": result.dfa.final_state,
                        "transitions": [{"from": s.previous, "symbol": s.token.category.value, "to": s.following}
                                        for s in result.dfa.trace]}}
