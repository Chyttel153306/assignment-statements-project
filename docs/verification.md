# Localhost migration verification

## Operator terminology and clean arrows on 23 October 2026

- Removed underscore marks from full-diagram labels. Arithmetic transitions
  now say "operators"; assignment and semicolon labels remain `=` and `;`.
- Removed the generic "symbol" group from rejecting arrows, and made those
  arrows solid. Validation rules and actual-input trace tokens are unchanged.
- JavaScript syntax checks and 538 DOM interaction assertions pass against
  the main server, including the new labels, navigation, and 51 laboratory cases.

## Simple rule diagram on 23 October 2026

- Simplified both diagrams to basic letter, digit, and symbol rules. Removed the
  long keyword/whitespace/error-category lists from diagram labels and tooltips.
  The complete table and backend still retain and enforce those transitions.
- Each rejection label uses at most two short lines. Symbols are grouped only
  when every member of `= + - * / ;` rejects in that state; otherwise only the
  specific rejecting punctuation is shown. Every visible category is derived
  from the actual runtime transition to Deadlock.
- Full DFA keeps generic rule labels during playback. The actual input remains
  available in arrow tooltips and the separate input-path view. Reduced the
  diagram height from 780 to 590 units after removing the long lists.
- JavaScript syntax checks passed. The main server serves the updated template
  and versioned renderer. DOM checks passed 534 assertions on the current page
  and 527 with legacy optional elements removed, including label correctness,
  the two-line limit, navigation, playback, and 51/51 laboratory cases.
- Browser-rendered visual quality remains unverified.

## Validator startup and stale page fix on 23 October 2026

- Reproduced the freeze at the main address: an older server served HTML without
  `help-dfa-svg`, while the current script constructed its diagram immediately.
  The resulting null-element exception occurred before navigation registration.
- Made new teaching elements optional during startup and synchronized diagram
  controls from the active renderer rather than stale HTML attributes.
- Enabled automatic template refresh. Homepage responses use `Cache-Control:
  no-store`; CSS and JavaScript URLs carry a hash of the current file contents.
- Identified two server processes listening on port 5000. Verified the obsolete
  process ran this project's `app.py`, stopped it, and confirmed the main address
  now serves the current sections and versioned assets.
- All 63 Python tests pass, including asset-version, HTML-cache, and running-app
  template-refresh regressions. Compilation and JavaScript parsing pass.
- On the repaired port 5000 server, all 502 current-page DOM assertions pass.
  Another 495 assertions pass with the new optional teaching elements removed
  and stale view-button attributes, covering navigation and real validation.
  Both runs include 13 validation requests and 51/51 laboratory cases.
- Browser-rendered visual quality remains unverified.

## Teaching sections and explicit rejection labels on 23 October 2026

- Grammar & Help contains four named sections: Regular Expression, Deterministic
  Finite Automaton (DFA), Transition Diagram, and Short Python Program. Topic
  buttons scroll to each section. The formal definition lists Q, the finite
  tokenizer alphabet, the transition function, the start state, and final states.
- The regex is rendered from a server constant and checked against the actual
  syntax results for all 51 laboratory cases. The page explains why a zero
  divisor can match the regex but still fail semantic validation.
- The second diagram uses the same runtime model and renderer as the playback
  diagram. SVG marker IDs are scoped per diagram to avoid conflicting arrows.
- Rejecting arrows list their exact runtime categories, including end-of-input
  failures. Their labels stay visible during playback, and tooltips also show
  the actual input read. Start still reads `int`; States 4 and 6 accept a digit
  and reject letters. No assignment grammar change was made.
- The Python example is the rendered source of `tools/recognize_assignment.py`.
  Subprocess checks verify valid, syntax-invalid, semantic-invalid, and prompted
  input, including exit codes and real DFA traces.
- All 60 Python tests pass; compilation and all three JavaScript syntax checks
  pass. The DOM harness passed 502 assertions against a fresh Flask instance on
  port 5007, including the four sections, both diagrams, unique SVG markers,
  exact rejection-category sets, playback, 13 validation requests, and all 51
  laboratory cases. It reads the server-rendered homepage.
- An older instance on port 5000 served a cached template, so a fresh port was
  used for verification. Restart existing Flask instances after these changes.
  DOM checks do not establish rendered browser or responsive visual quality.

## Numbered diagram and deadlocks on 23 October 2026

- Full DFA is the default diagram view. Its nodes show Start, States 2–7, Final,
  and Deadlock. Final retains its double circle. The same labels appear in input
  paths, diagram tooltips, and the diagram playback status.
- Deadlock arrows are visible by default, including the absorbing "all input"
  self-loop. Each ordinary state has an "otherwise" arrow; its tooltip lists
  the backend categories that actually reject in that state. Rejecting paths are
  routed below the main sequence, with enough room for the trap and its loop.
- The engine still uses A–H plus DEAD. Its grammar, trace IDs, API contract, and
  syntax/semantic separation are preserved.
- All 56 Python tests pass. JavaScript syntax checks and 483 DOM interaction
  assertions passed against the live API, including the default full diagram,
  numbered labels, Final double circles, all deadlock arrows, path switching,
  replay, 13 validation requests, and the 51-case laboratory.
- DOM verification does not establish browser-rendered or responsive appearance.

## Reference document review on 23 October 2026

- The user confirmed the final assignment test-case table governs the system.
  All 16 examples match through both core validation and real HTTP requests.
- Added the three exact reference examples absent from the laboratory, bringing
  it to 51 cases. Existing cases are retained. Live laboratory result: 51/51.
- All 56 Python unittest tests pass. New tests cover the reference outcomes,
  separate syntax and semantics, laboratory inclusion, and exclusion of the
  conflicting plain-assignment/password languages.
- Corrected the operator hint to show ASCII `-` and `*`. JavaScript parsing
  passed for all three scripts; the existing DOM harness passed 461 assertions
  against the live API, with 13 validation requests and all 51 laboratory cases.
- Python compilation passed; regenerated transition documentation is unchanged.
- Browser inventory was empty. Rendered layout and responsive visual checks
  remain unverified. Prior verification entries below are historical.

See [the reference review](reference_review.md) for the discrepancies, exact
reference outcomes, and changes.

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
