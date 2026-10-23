# Restricted assignment grammar

The final assignment test-case table in `Assignment_Recognizer_Documentation.docx`
is the agreed specification, confirmed by the user on 23 October 2026. Its 16
examples are checked by `tests/test_documentation.py` through both the core and
the JSON API, and all are available in the Test Laboratory. The document's earlier
plain-assignment rules and password code describe different languages; see
[the reference review](reference_review.md) for the discrepancies.

## Grammar

```text
assignment ::= WS? "int" WS identifier WS? "=" WS? expression WS? ";" WS? EOF
identifier ::= (letter | "_") {letter | digit | "_"}
expression ::= integer WS? operator WS? integer
               {WS? operator WS? integer}
integer    ::= digit {digit}
operator   ::= "+" | "-" | "*" | "/"
letter     ::= "A".."Z" | "a".."z"
digit      ::= "0".."9"
WS         ::= (space | tab) {space | tab}
```

At least one operator is required. Spaces or tabs MUST separate int and the identifier.
Leading and trailing spaces/tabs are allowed. Line breaks are rejected.
Names and digits use the ASCII alphabet. The identifier spelling int is allowed
by this restricted grammar (this is not a full C or Python language validator).

The following regular expression describes the syntax when used with Python's
`re.fullmatch`. It is a specification and test oracle; runtime recognition uses
the explicit DFA. The separate semantic check still rejects literal zero divisors.

```regex
[ \t]*int[ \t]+[A-Za-z_][A-Za-z_0-9]*[ \t]*=[ \t]*[0-9]+(?:[ \t]*[+*/-][ \t]*[0-9]+)+[ \t]*;[ \t]*
```

Accepted: int a = 8 + 8;
Accepted: int sum = 1+2+3-8*2/8;
Accepted: int x_1 = 8/05;
Rejected: int a = 8;       (no arithmetic operator)
Rejected: int a = 5++5;    (missing operand)
Rejected: int a = 8/00;    (semantic division by zero)

Syntax and semantics are separate. The DFA accepts literal zero division as
syntactically well formed; the semantic checker then rejects any all-zero integer
immediately following /. Leading zeros are decimal digit strings, not octal.

Unsupported: variable operands, unary signs, parentheses, decimals, comments,
other types, non-ASCII names, multiple statements, and equality operators.
The application recognizes syntax; it does not evaluate expressions or check
overflow, variable declarations, arithmetic precedence, or computed denominators.
No Python eval() or arbitrary code execution is used.

Trace indices are 1-based token positions INCLUDING whitespace and EOF.
Character locations shown in the UI are 1-based; core spans are 0-based [start,end).

## A–H DFA and lexical boundaries

A is the start; H is the only accepting state, and acceptance requires the final
EOF token. DEAD rejects every continuation. A → B reads the lexical INT unit:
the exact keyword `int` together with its required space/tab separator. Its trace
span includes that separator. If the separator is absent, MISSING_SPACE leads to
DEAD. Identifiers and numbers are then read one ASCII character at a time.
Whitespace between two word/number lexemes is WORD_GAP and leads to DEAD, so
ignoring optional boundary whitespace cannot join `ab cd` or `12 34`.

B → C starts a name; C loops on letters, digits, and underscores. C → D reads =.
D → E reads the first digit; E loops on digits and requires an operator to F.
F → G reads the next operand's first digit. G loops on digits (the approved
correction to the proposed G → E edge), returns to F on an operator, and reads
the semicolon into H. Optional boundary spaces/tabs loop without changing states.
H loops on trailing whitespace and EOF, but cannot accept a stream missing EOF.

The original whole-lexeme tokenizer is retained for literal division-by-zero
checking. The execution trace, diagram path, and error token indices use the
character token stream. Semantic errors point to the first divisor digit and
retain the entire divisor's character span, including multiple leading zeros.
