"""Regression tests for the requested A–H machine and approved G digit loop."""
import random
import re
import unittest

from app import create_app
from core.dfa_engine import (ACCEPTING_STATES, INITIAL_STATE, STATES, execute, transition)
from core.tokenizer import Category as C, tokenize, tokenize_for_dfa
from core.validator import validate


class StateDesignTests(unittest.TestCase):
    def test_exact_states_and_requested_moves(self):
        self.assertEqual(set(STATES), set("ABCDEFGH") | {"DEAD"})
        self.assertEqual(INITIAL_STATE, "A")
        self.assertEqual(ACCEPTING_STATES, {"H"})
        expected = {
            ("A", C.KEYWORD): "B", ("B", C.LETTER): "C", ("B", C.UNDERSCORE): "C",
            ("C", C.LETTER): "C", ("C", C.UNDERSCORE): "C", ("C", C.DIGIT): "C",
            ("C", C.ASSIGN): "D", ("D", C.DIGIT): "E", ("E", C.DIGIT): "E",
            ("E", C.OPERATOR): "F", ("F", C.DIGIT): "G", ("G", C.DIGIT): "G",
            ("G", C.OPERATOR): "F", ("G", C.SEMICOLON): "H", ("H", C.EOF): "H",
        }
        for pair, following in expected.items():
            with self.subTest(pair=pair):
                self.assertEqual(transition(*pair), following)
        self.assertEqual(transition("E", C.SEMICOLON), "DEAD")

    def test_all_user_examples(self):
        valid = ("int a = 8+8;", "int ab = 8+8+8;", "int sum = 1+2+3-8*2/8;")
        invalid = ("int a = 8;", "int 1a = 5+5;", "int a = 5++5;",
                   "int a = 5+;", "int a = 5+5", "int a = 8+8;;")
        for source in valid + invalid:
            with self.subTest(source=source):
                self.assertEqual(validate(source).accepted, source in valid)

    def test_existing_lexical_execute_callers_are_supported(self):
        for source in ("int a=12+34;", "int ab=1++2;", "int _id=1+2+3;"):
            with self.subTest(source=source):
                self.assertEqual(execute(tokenize(source)), execute(tokenize_for_dfa(source)))

    def test_identifier_is_read_character_by_character(self):
        result = validate("int _ab12=8+9;")
        characters = [step for step in result.dfa.trace if step.previous == "B" or step.previous == "C" and step.following == "C"]
        self.assertEqual([step.token.text for step in characters], list("_ab12"))
        self.assertEqual([step.following for step in characters], ["C"] * 5)

    def test_multi_digit_integer_paths_do_not_merge_first_and_later_operands(self):
        result = validate("int ab=123+456+78;")
        self.assertTrue(result.accepted)
        moves = [(step.token.text, step.previous, step.following) for step in result.dfa.trace if step.token.category == C.DIGIT]
        self.assertEqual(moves, [("1", "D", "E"), ("2", "E", "E"), ("3", "E", "E"),
                                 ("4", "F", "G"), ("5", "G", "G"), ("6", "G", "G"),
                                 ("7", "F", "G"), ("8", "G", "G")])
        self.assertFalse(validate("int ab=123;").accepted)
        self.assertTrue(validate("int ab=1+123;").accepted)

    def test_repeated_operations_and_leading_zeros(self):
        for source in ("int a=12+34-56*78/005;", "int a=000+000;", "int a=10/05+120/0003;"):
            with self.subTest(source=source):
                self.assertTrue(validate(source).accepted)

    def test_missing_operands_and_repeated_operators(self):
        for source in ("int a=;", "int a=+1+2;", "int a=1+;", "int a=1+", "int a=1++2;",
                       "int a=1**2;", "int a=1//2;", "int a=1+-2;", "int a=1+2/*3;"):
            with self.subTest(source=source):
                self.assertFalse(validate(source).accepted)

    def test_whitespace_is_allowed_only_at_lexical_boundaries(self):
        for source in (" \tint\t_name12 \t=\t 123 \t+\t45 \t; \t", "int int=12+34;"):
            with self.subTest(source=source):
                self.assertTrue(validate(source).accepted)
        for source in ("inta=1+2;", "int=1+2;", "int\na=1+2;", "int ab cd=1+2;",
                       "int a b=1+2;", "int a=12 34+5;", "int a=1+2 3;", "int a=1+2\t3;"):
            with self.subTest(source=source):
                self.assertFalse(validate(source).accepted)

    def test_invalid_names_and_unsupported_syntax(self):
        for source in ("int 1a=1+2;", "int 12=1+2;", "int a==1+2;", "int a=1.2+3;",
                       "int a=(1+2);", "int a=x+2;", "int a=1+y;", "int a=1+2;\n", "int a=1+2; int b=2+3;"):
            with self.subTest(source=source):
                self.assertFalse(validate(source).accepted)

    def test_h_requires_completed_input(self):
        tokens = tokenize_for_dfa("int a=12+34;")
        truncated = execute(tokens[:-1])
        self.assertEqual(truncated.final_state, "H")
        self.assertFalse(truncated.accepted)
        complete = execute(tokens)
        self.assertTrue(complete.accepted)
        self.assertEqual(complete.trace[-1].token.category, C.EOF)
        self.assertEqual((complete.trace[-1].previous, complete.trace[-1].following), ("H", "H"))
        for suffix, accepted in ((" \t", True), (";", False), ("x", False), ("1", False)):
            with self.subTest(suffix=suffix):
                self.assertEqual(validate("int a=12+34;" + suffix).accepted, accepted)

    def test_dfa_token_stream_is_lossless_and_has_exact_spans(self):
        for source in (" \tint\t_ab12 = 001 + 234; \t", "int a=12 34+5;", "int=1+2;", "inta=1+2;"):
            with self.subTest(source=source):
                tokens = tokenize_for_dfa(source)
                self.assertEqual("".join(token.text for token in tokens), source)
                for token in tokens:
                    self.assertEqual(token.text, source[token.start:token.end])
        keyword = tokenize_for_dfa("int\ta=1+2;")[0]
        self.assertEqual((keyword.category, keyword.text), (C.KEYWORD, "int\t"))

    def test_error_location_and_semantic_digit_index_match_the_trace(self):
        for source in ("int a=12++34;", "int a=12+;", "int a=12+34", "int a=12/000;"):
            with self.subTest(source=source):
                result = validate(source)
                token = result.tokens[result.error_token_index-1]
                self.assertEqual(token.start, result.error_start)
                self.assertEqual(result.dfa.trace[result.error_token_index-1].token, token)
        missing_space = validate("int=1+2;")
        self.assertEqual(missing_space.error_start, 3)

    def test_semantics_remain_separate(self):
        for divisor in ("0", "00", "0000"):
            result = validate(f"int a=123/{divisor};")
            self.assertTrue(result.syntax_accepted)
            self.assertEqual(result.dfa.final_state, "H")
            self.assertFalse(result.accepted)
            self.assertEqual(result.source[result.error_start:result.error_end], divisor)
        self.assertTrue(validate("int a=123/0005;").accepted)

    def test_api_graph_and_trace_use_exact_a_through_h_states(self):
        client = create_app({"TESTING": True}).test_client()
        graph = client.get("/api/dfa").get_json()
        self.assertEqual({state["id"] for state in graph["states"]}, set("ABCDEFGH") | {"DEAD"})
        self.assertEqual(graph["accepting_states"], ["H"])
        result = client.post("/api/validate", json={"statement": "int sum=12+34+56;"}).get_json()
        self.assertEqual(result["state_path"][0], "A")
        self.assertEqual(result["state_path"][-1], "H")
        self.assertIn("LETTER", [step["category"] for step in result["trace"]])
        self.assertIn("DIGIT", [step["category"] for step in result["trace"]])
        self.assertEqual(result["state_path"], ["A"]+[step["next_state"] for step in result["trace"]])

    def test_existing_response_fields_are_preserved(self):
        client = create_app({"TESTING": True}).test_client()
        for source in ("int a=12+34;", "int a=12/00;", "int a=12+;"):
            result = client.post("/api/validate", json={"statement": source}).get_json()
            self.assertEqual(set(result), {"input", "accepted", "syntax_accepted", "semantic_accepted",
                "message", "error", "final_state", "trace", "state_path", "diagram"})
            self.assertEqual(set(result["diagram"]), {"current_state", "transitions"})
            for step in result["trace"]:
                self.assertEqual(set(step), {"step", "token", "display", "category", "start", "end",
                    "previous_state", "next_state", "symbol", "transition", "explanation"})
            if result["error"]:
                self.assertEqual(set(result["error"]), {"type", "message", "start", "end", "character", "token_index"})

    def test_supplementary_regex_oracle_for_mutated_inputs(self):
        # A test oracle only. Runtime acceptance is exclusively the explicit DFA.
        reference = re.compile(r"[ \t]*int[ \t]+[A-Za-z_][A-Za-z_0-9]*[ \t]*=[ \t]*[0-9]+(?:[ \t]*[+*/-][ \t]*[0-9]+)+[ \t]*;[ \t]*")
        rng = random.Random(87)
        for base in ("int a=12+34;", "int _name9 = 000+005-67/00;", " int int=123*45+6; "):
            for _ in range(350):
                location = rng.randrange(len(base)+1)
                source = base[:location] + rng.choice((" ", "\t", "\n", "a", "_", "1", ";", "+", "=", ".", "")) + base[location:]
                with self.subTest(source=source):
                    self.assertEqual(validate(source).syntax_accepted, reference.fullmatch(source) is not None)


if __name__ == "__main__":
    unittest.main()
