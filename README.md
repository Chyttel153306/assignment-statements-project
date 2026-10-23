# Assignment Statement DFA Validator

A localhost web application for **Design and Implementation of an Assignment
Statement Validator Using Deterministic Finite Automata (DFA)**. The existing
Python tokenizer, semantic checker, grammar, test cases, and original test coverage
are preserved. The explicit DFA now uses the requested A-H design. Flask, HTML, CSS, vanilla JavaScript, and dynamic SVG replace the
desktop interface. No Node.js runtime, build step, CDN, hosting, or account is needed.

The final assignment test-case table in the supplied reference document is the
agreed specification. All 16 examples pass. The reference also contains conflicting
plain-assignment rules and password code; see the [reference review](docs/reference_review.md)
for the findings and verification results.

## Run on Windows

With Python **3.10 or newer**, from this project directory:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000**. Keep the terminal open; press **Ctrl+C** to stop.
Debug mode is disabled, and Flask binds only to `127.0.0.1`. Its development
server is sufficient for this local teaching project.

Using the existing project environment (already installed in this workspace):

```powershell
.\.venv\Scripts\python.exe app.py --open
```

Or double-click **run_windows.bat**. It prefers `.venv`, checks Python and Flask,
prints the correct installation command if dependencies are missing, starts the
server, and opens the default browser after the health endpoint responds. It
does not automatically install packages. The terminal stays open.
`python main.py` remains a compatibility entry point for the same web app.

If Python is not on PATH or the Windows Store alias fails, use `py -3` or the
full path to a working Python. To create an isolated environment:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run_windows.bat
```

Installation needs internet access once; normal use is offline. For offline
setup, use `python -m pip download -r requirements.txt -d wheels` on a connected
computer, copy the wheels, then run
`python -m pip install --no-index --find-links wheels -r requirements.txt`.
Tkinter and Tcl/Tk are no longer needed.

## Pages and interactions

The **Validator** opens first. Enter `int total = 8 + 5;` and click **Check
Statement**, or press **Ctrl+Enter**. Rejections explain the problem and identify
the character/token location. Syntax and semantic results are shown separately.

- **Dashboard:** quick guide, examples, manual accepted/rejected counts, and latest
  laboratory pass count. Statistics belong to this tab and reset on refresh.
- **Validator:** editable input, loading and duplicate-submission protection,
  clear, valid/invalid examples, real backend results, friendly errors, view links.
- **DFA Diagram:** backend-defined SVG states and arrows, incoming start arrow,
  double accepting circles, DEAD, tooltips, legend, visited/current/failure
  highlighting, reset/full path/fit/zoom, and optional expansion of rejecting arrows.
- **Validation Steps:** actual token trace, explanations, previous/next/reset,
  direct step selection, and a button to locate the current row. Playback and
  diagram highlighting remain synchronized.
- **Test Laboratory:** 51 real checks, expected/actual/PASS/FAIL, totals, search,
  validity/outcome filters, failed-expectation explanations, and loading into Validator.
- **Grammar & Help:** Regular Expression, formal Deterministic Finite Automaton
  (DFA) definition, a Transition Diagram, and a runnable Short Python Program,
  plus grammar, examples, mistakes, the complete runtime transition table, FAQ,
  and limitations. All four sections have direct topic buttons.

Navigation does not reload the page. Input remains intact across navigation and
request failures. Editing marks the result as stale until checked again. Diagram
and steps retain the **last checked input**, labeled in each view. Lab runs do not
overwrite manual traces. Reset controls reset playback, not validation history.
The diagram uses a single left-to-right row and shows only meaningful symbols;
SPACE/EOF loops and long state captions are omitted. Normal playback and state
path summaries skip formatting moves. Enable **Show whitespace details** on the
Validation Steps page to inspect the complete engine trace. Spacing rules and
EOF acceptance are still checked by the unchanged backend; formatting-related
rejections remain visible. The full diagram shows Deadlock and its rejecting
arrows by default. The deadlock-arrow control can hide unused rejecting arrows.
Responsive navigation, labeled controls, focus indicators, status announcements,
notifications, reduced-motion support, and contained scrolling are included.

## Grammar (unchanged)

```text
assignment ::= int identifier = expression ;
identifier ::= (letter | _) {letter | digit | _}
expression ::= integer operator integer {operator integer}
integer    ::= digit {digit}
operator   ::= + | - | * | /
```

At least one space/tab must follow lowercase `int`. Other spaces/tabs are optional
between tokens and before/after the statement. Names start with ASCII letters or
`_`; remaining characters may also include ASCII digits. The existing grammar
permits `int` as a variable name. Leading-zero integers are allowed. At least one
arithmetic operator is required.

Valid: `int a = 8 + 8;`, `int a=3+4+4;`,
`int sum = 1+2+3-8*2/8;`, `int x_1 = 10 / 5;`, `int a = 8/05;`.

Invalid: `int a = 8;`, `inta = 5+5;`, `int 1a = 5+5;`, `int a = 5+;`,
`int a = 5+5`, `int a = 5++5;`, `int a = x + 1;`, `int a = 8/0;`,
`int a = 8/00;`, and `int a = 8+8;;`.

The DFA checks **syntax**. A separate checker rejects literal all-zero divisors
without evaluating input. `int a=8/00;` correctly reaches **H** in its syntax
trace but is finally rejected for division by zero. Syntax failures skip semantics.
Green trace arrows mean allowed syntax moves, not overall semantic acceptance.

Unsupported: right-hand variables, unary signs, parentheses, decimals, comments,
newlines, Unicode names/digits, other types, multiple statements, and `==`.
This is a restricted teaching language, not full Python or C. It does not compute
results, check overflow, or execute user input. See the
[grammar specification](docs/grammar.md) and [transition table](docs/transition_table.md).

## Architecture

```text
app.py                        Local server and --open option
main.py                       Compatibility web launcher
app/__init__.py               Flask factory and API routes
app/presentation.py           JSON and friendly explanation adapters
core/                         Preserved tokenizer, DFA, validator, semantics
templates/index.html          Six-page HTML workspace
static/css/style.css          Shared responsive design system
static/js/app.js              API, navigation, session and playback state
static/js/dfa_visualizer.js   SVG view of backend graph and execution
data/test_cases.json          51 laboratory expectations including all reference examples
tests/                        Original tests and API contract tests
tools/export_transition_table.py  Generate documentation from runtime definitions
archive/                      Recoverable desktop source backup
```

The DFA defines **A–H plus DEAD**, with A initial and H accepting only after
EOF. All 108 state/category pairs map to exactly one state; DEAD is absorbing.
Identifiers and integer literals are read one character at a time. E loops on
digits of the first operand; G loops on digits of later operands, as approved
to distinguish `int a=12;` (rejected) from `int a=1+12;` (accepted). Execution
consumes EOF before acceptance or stops at
the first rejecting move, retaining it in the trace. The API, graph, trace,
transition table, and laboratory use the same engine. JavaScript computes only
view positions and paths; it never reimplements recognition. JSON adapters give
plain-English explanations based on the actual state, token, and result.

The lexical INT unit includes the required space/tab separator. WORD_GAP marks
whitespace between word/number lexemes, preventing split identifiers and numbers.
MISSING_SPACE rejects an `int` keyword without its required separator. Other
spaces/tabs remain visible SPACE tokens. The original whole-lexeme tokenizer
continues to feed the separate semantic checker; diagram and trace tokens are
character-level. A semantic error's token index identifies its first divisor
digit, while its character span covers the whole divisor.

The former desktop files are preserved in
`archive/desktop_before_web_migration.zip` and removed from active source to
avoid conflicting interfaces. See [backup notes](archive/README.md). Old GUI
packages may remain in an existing `.venv`, but are no longer required or imported.

## JSON API

| Method | Endpoint | Response |
| --- | --- | --- |
| GET | `/api/health` | Backend status |
| POST | `/api/validate` | Real result, error, trace, state path, diagram moves |
| GET | `/api/dfa` | States, alphabet, start/accepting/dead states, transitions, grouped edges |
| GET | `/api/examples` | Predefined cases, expectations, purposes, IDs |
| POST | `/api/test-cases/run` | Actual case results and total/passed/failed counts |

Validation body: `{"statement":"int total = 8 + 5;"}` with JSON content type.
Response fields: `input`, `accepted`, `syntax_accepted`, `semantic_accepted`
(`null` when not run), `message`, `error`, `final_state`, `trace`, `state_path`,
and `diagram`. Errors include `type`, message, zero-based `[start,end)` character
spans, a one-based `character`, and one-based `token_index`. Indices include
spaces/tabs and EOF. EOF errors point just after the last character. Each trace
row contains the actual token, category, origin, transition, destination, and
explanation; diagram moves match it exactly.

Malformed JSON, missing fields, wrong types, unsupported methods, and unexpected
errors return friendly JSON and appropriate HTTP codes. Both accepted and
rejected well-formed requests return HTTP 200. To keep the UI responsive, the API
limits input to **20,000 characters** and requests to **128 KiB**. This does not
change the preserved core grammar. Internal details are logged only to the terminal.

## Tests and verification

The diagram opens on **Full DFA**, showing **Start → State 2 → State 3 → State 4
→ State 5 → State 6 → State 7 → Final**. The accepting Final state has double
circles. Solid arrows show simple letter, digit, and operator rejection rules
and lead to a shared
**Deadlock** state, whose "all input" self-loop makes it absorbing. Deadlock
arrows are visible by default. These diagram labels correspond to A–H and DEAD
in the engine trace; recognition and API state IDs are unchanged.

Full DFA keeps its rule labels during playback; actual input appears in the
arrow tooltip and Your Input Path. Rejection labels use at most two short lines.
Arithmetic inputs are labelled **operators** instead of listing `+ - * /`.
The diagram omits underscore labels; the complete table retains that rule.
Assignment `=` and semicolon `;` keep their own labels. Start requires the `int`
keyword and separator. States 4 and 6 require a digit and reject letters.
Detailed whitespace and end-of-input rules remain in the complete transition
table and are still enforced by the machine.

**Your Input Path** shows each meaningful move as its own
node and an arrow labeled with the actual input; repeated states keep their
numbered labels. Spaces are hidden. Paths longer than 24 moves have Earlier/Later
controls so labels remain readable. Playback follows the selected trace step and
automatically opens its part. **Full DFA** shows the complete fixed A–H machine
and its loops. Switching views preserves the checked statement and playback.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m compileall -q app core tests tools app.py main.py
.\.venv\Scripts\python.exe tools/export_transition_table.py
```

**63 tests pass**, including frontend-delivery regressions, all 16 reference
examples through the core and API,
the original coverage updated for A–H and API formats, malformed
requests, limits, failures, actual laboratory results, and exact graph/trace/path
agreement for all 51 cases. Original coverage includes 200 generated valid
assignments, 600 invalid mutations, and long-integer checks. New state-design
tests cover all requested examples, every specified move, the corrected G digit
loop, lexical whitespace boundaries, character spans, EOF-gated H acceptance,
and a supplementary regex oracle for 1,050 mutated inputs. Runtime syntax
validation uses the explicit DFA exclusively.

The server was started and live health/index/laboratory endpoints checked (51/51
passed). All three JavaScript files passed syntax checks, and 538 isolated DOM
interaction assertions passed against the live API. Browser automation reported
no available browsers, so visual layout, responsive rendering, and browser
interaction flows could not be visually verified. See [verification notes](docs/verification.md).

The Short Python Program shown in Grammar & Help is the actual source of
`tools/recognize_assignment.py`. Run it from the project folder:

```powershell
.\.venv\Scripts\python.exe -m tools.recognize_assignment "int a = 8 + 8;"
```

It uses the same DFA and semantic checker as the web app and prints the real
transition trace. Omit the argument for a prompt. Exit codes are 0 for valid and
1 for invalid statements. HTML templates refresh automatically and script/style
URLs are versioned by file content. New optional Help sections cannot prevent an
older page from starting. Restart the server after Python code changes, then
refresh the browser. Keep one server instance on port 5000.
