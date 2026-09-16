# PA 3: The USILang Parser

Full assignment: `PA_03_The_USILang_Parser.md`.

## Setup
Paste your own completed PA 2 `tokenize()` into `lexer.py` first (see
the note at the top of that file) -- `parser.py` imports it.

## Run
```bash
python test_parser.py
```
Complete the parsing functions in `parser.py` (AST node types are
already defined). The harness structurally compares your AST against
expected shapes for valid programs (checking precedence and
left-associativity), and confirms invalid programs raise `ParseError`.
Success Token prints once every check passes.

## Submit
1. `PA3_Theory.pdf` (or `.md`)
2. `parser.py` (and your working `lexer.py`)
3. The Success Token
