# Assignment recognizer reference review

Reviewed on 23 October 2026 against
`D:\DOWNLOADS\Assignment_Recognizer_Documentation.docx`.

The system matches all 16 examples in the document's final assignment test-case
table. The user confirmed that this table governs the implementation. The
existing assignment DFA and division-by-zero checker already produced the correct
results; no recognition-rule change was needed.

## Agreed behavior

An assignment starts with lowercase `int` followed by a space or tab and an
identifier. Identifiers contain ASCII letters, digits, and underscores, and cannot
start with a digit. The right side contains unsigned integer operands and at least
one arithmetic operator from `+ - * /`. A single semicolon terminates the statement.
Spaces and tabs may separate tokens. Leading zeros are allowed, but a divisor
made entirely of zeros is rejected by a separate semantic check.

The [grammar](grammar.md) and [runtime transition table](transition_table.md)
describe the complete supported language, including the existing extensions for
underscore-first names, tabs, and leading/trailing boundary whitespace. The final
table explicitly confirms underscores within names; it does not independently
specify every one of these lexical choices.

## Conflicts in the supplied document

| Document section | Discrepancy | Resolution for the system |
| --- | --- | --- |
| Earlier assignment rules and examples | Allow omitted `int`, a single operand, and variables on the right side; the final table rejects those forms. | Follow the final table, as confirmed by the user. |
| Identifier rule | Earlier prose limits names to letters and digits; a final valid example includes an underscore. | Retain underscore support. |
| Password headings and Python sample | Check a letter/digit prefix, a special symbol, and a numeric suffix. This is a different language. | Keep assignment recognition as the application purpose. |
| q0 to q5 transition table and diagram description | Describe the password recognizer, including its accepting q4, rather than assignment token order. | Retain the application's assignment-specific A to H DFA plus DEAD. |
| Formal regular expression section | No readable expression appears in the document text. | Add the assignment syntax expression to `docs/grammar.md`. |

The attached Word document was read for requirements and was not modified. Its
password code was not adopted as an implementation instruction.

## Reference examples checked

| Input | Expected and actual outcome | Check responsible for rejection |
| --- | --- | --- |
| `int a = 8 + 8;` | Valid | None |
| `int a=3+4+4;` | Valid | None |
| `int sum = 1+2+3-8*2/8;` | Valid | None |
| `int x_1 = 10 / 5;` | Valid | None |
| `int a = 8/05;` | Valid | None |
| `int a = -5;` | Invalid | Syntax: unary minus |
| `int a = 8/0;` | Invalid | Semantics: zero divisor |
| `int a = 8 / 00;` | Invalid | Semantics: zero divisor |
| `int a = 8;` | Invalid | Syntax: arithmetic operation required |
| `inta = 5+5;` | Invalid | Syntax: missing keyword separator |
| `int 1a = 5+5;` | Invalid | Syntax: identifier starts with a digit |
| `int a = 5++5;` | Invalid | Syntax: consecutive operators |
| `int a = 5+;` | Invalid | Syntax: missing operand |
| `int a = 5+5` | Invalid | Syntax: missing semicolon |
| `int a = 5+5;;` | Invalid | Syntax: extra semicolon |
| `int a = x + 1;` | Invalid | Syntax: variable operand |

Zero-division examples correctly finish the syntax trace at H and are then
rejected by semantics. Syntax failures enter DEAD and do not run semantics.

## Changes made

- Added the three exact reference examples missing from the Test Laboratory:
  unary minus, a spaced all-zero divisor, and an extra semicolon. Existing cases
  and their IDs remain intact. The laboratory now contains 51 cases.
- Added regression coverage for all 16 reference examples through both the core
  validator and Flask API, including syntax/semantic outcomes and final states.
  Additional checks ensure these examples stay available in the laboratory and
  the conflicting plain-assignment/password languages remain rejected.
- Corrected the editor's supported-operator hint to show the actual ASCII `-`
  and `*` characters in place of typographic minus and multiplication signs.
- Recorded the agreed specification and added the syntax regular expression.

## Verification results

- All 56 Python unittest tests passed, including existing generated-input,
  long-integer, request-error, transition-totality, and trace consistency checks.
- All 16 reference cases matched through actual HTTP validation requests:
  5 accepted, 9 rejected by syntax, and 2 rejected by semantics.
- Live health and homepage requests succeeded; the live laboratory returned
  51 passed, 0 failed.
- All three frontend JavaScript files parsed successfully. The existing isolated
  DOM interaction harness passed 461 assertions against live Flask responses,
  covering 13 validation requests, navigation, playback, diagrams, filtering,
  error focus, and all 51 laboratory cases.
- Python compilation passed. Regenerating the runtime transition table produced
  no change to the table.

Browser inventory contained no connected browsers. DOM checks do not establish
rendered visual quality or responsive layout; those remain unverified.

To repeat the Python checks from the project directory:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m compileall -q app core tests tools app.py main.py
```
