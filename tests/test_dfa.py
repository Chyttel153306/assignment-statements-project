import unittest
from core.tokenizer import Category as C, tokenize_for_dfa as tokenize
from core.dfa_engine import (STATES, ALPHABET, TRANSITIONS, ACCEPTING_STATES,
                             DEAD_STATE, INITIAL_STATE, execute, grouped_transitions, transition)


class DFATests(unittest.TestCase):
    def test_transition_function_is_total_and_closed(self):
        self.assertEqual(len(TRANSITIONS), len(STATES)*len(ALPHABET))
        for state in STATES:
            for category in ALPHABET:
                self.assertIn(transition(state, category), STATES)
        self.assertEqual(ACCEPTING_STATES, {"H"})
        self.assertEqual(INITIAL_STATE, "A")
        self.assertEqual(set(STATES), set("ABCDEFGH") | {"DEAD"})

    def test_dead_state_absorbs_every_category(self):
        for category in ALPHABET:
            self.assertEqual(transition(DEAD_STATE, category), DEAD_STATE)

    def test_exact_execution_path(self):
        result = execute(tokenize("int a=1+2;"))
        self.assertTrue(result.accepted)
        self.assertEqual([step.following for step in result.trace],
                         ["B", "C", "D", "E", "F", "G", "H", "H"])

    def test_trace_uses_transition_function(self):
        for source in ("int a=1+2+3;", "int a=1++2;", "", "int a=1+2;;", "int a=8/00;"):
            result = execute(tokenize(source))
            previous = INITIAL_STATE
            for number, step in enumerate(result.trace, 1):
                self.assertEqual(step.number, number)
                self.assertEqual(step.previous, previous)
                self.assertEqual(step.following, TRANSITIONS[step.previous, step.token.category])
                previous = step.following
            self.assertEqual(previous, result.final_state)

    def test_eof_is_required_for_acceptance(self):
        self.assertFalse(execute(tokenize("int a=1+2;")[:-1]).accepted)

    def test_rejection_transition_is_retained(self):
        result = execute(tokenize("int a=1++2;"))
        self.assertFalse(result.accepted)
        self.assertEqual(result.trace[-1].previous, "F")
        self.assertEqual(result.trace[-1].token.text, "+")
        self.assertEqual(result.trace[-1].following, DEAD_STATE)

    def test_diagram_groups_preserve_every_transition(self):
        expanded = {(previous, category): following
                    for (previous, following), categories in grouped_transitions().items()
                    for category in categories}
        self.assertEqual(expanded, TRANSITIONS)

    def test_syntax_accepts_zero_division(self):
        self.assertTrue(execute(tokenize("int a=8/00;")).accepted)


if __name__ == "__main__":
    unittest.main()
