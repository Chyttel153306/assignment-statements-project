"""Run from the project folder: python -m tools.recognize_assignment 'int a=1+2;'"""
import argparse

from core.validator import validate


def main():
    parser = argparse.ArgumentParser(description="Assignment statement DFA recognizer")
    parser.add_argument("statement", nargs="?", help="Assignment to check; prompts if omitted")
    args = parser.parse_args()
    source = args.statement if args.statement is not None else input("Assignment: ")
    result = validate(source)
    print(f"{'VALID' if result.accepted else 'INVALID'}: {result.message}")
    for step in result.dfa.trace:
        print(f"{ascii(step.token.display)}: {step.previous} --{step.token.category.value}--> {step.following}")
    return 0 if result.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
