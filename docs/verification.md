# Localhost migration verification

## A–H state-design update

- A–H plus DEAD implemented with an explicit total transition dictionary. G loops
  on digits as approved, keeping first and later operands distinguishable.
- Identifier characters and integer digits are actual individual DFA moves.
  Keyword separation and split-word whitespace are explicit lexical classes.
- All **53 tests passed**, including all requested examples, 1,050 supplementary
  regex-oracle mutations, EOF-gated H acceptance, malformed inputs, semantic
  separation, and graph/trace/path agreement. Existing 48 laboratory cases pass.
- Flask route definitions, API field names, the semantic checker, and frontend
  stylesheet are preserved. Transition documentation is generated from runtime
  definitions. The prior migration record below is historical.
- Live API checks confirmed A–H plus DEAD, the requested accepted examples,
  rejection of `int a=12;`, acceptance of `int a=1+12;`, and 48/48 laboratory
  results. All 114 isolated DOM interaction assertions passed against the live
  updated API, including graph rendering and synchronized trace replay. Frontend
  JavaScript syntax checks passed. Browser inventory was empty, so visual browser
  inspection remains unverified.

22 October 2026 · Windows · Python 3.14.7 · Flask 3.1.3

- Inspected desktop source, four core modules, tests, grammar, data, Canvas
  renderer, and launch files. All original 25 tests passed before migration.
- Preserved tokenizer, DFA execution/transitions, semantic checker, grammar,
  48 expectations, and original tests. Only the validator docstring changed.
- **37 unittest tests passed**, including all original coverage, 48 case
  expectations, 200 generated valid assignments with 600 invalid mutations,
  request formats/limits/errors, and exact graph/trace/path/diagram agreement.
- Started `http://127.0.0.1:5000`. Live health and index returned **200**.
  A real HTTP laboratory POST returned **48 total, 48 passed, 0 failed**.
- Both JavaScript files passed syntax parsing in the available V8 runtime.
  No Node.js runtime is needed by the application.
- HTML structure checks passed: all six pages exist, IDs are unique, and every
  direct JavaScript element reference resolves. Python compilation and the
  compatibility launcher's `--help` check passed.
- Archived the desktop modules in a verified ZIP before removing obsolete active
  sources. No original core tests or data were deleted.
- Browser inventory returned **no available browsers**; attempting Edge returned
  `Browser is not available: edge`. Rendered layout, screenshots, responsive
  appearance, and browser interaction flows could not be tested. The OS default
  browser launch returned success; it does not prove visual or interactive QA.

The earlier desktop verification record is retained in the desktop backup ZIP.

## Input path and full DFA views

- All 53 Python unittest tests pass after this frontend-only change.
- JavaScript syntax parsing passed. Isolated DOM integration against the live
  Flask API passed 461 assertions, including 13 validation requests and 48/48
  laboratory cases. Checks compare expanded node sequences and individual input
  labels with the real backend trace, repeated states, invalid paths, reset and
  replay, view switching, and pagination of a long expression.
- The input view uses up to 24 transitions per part; the fixed full-machine view
  and backend response formats are preserved.
- These are DOM checks, not rendered browser or responsive-layout verification.
