# PA 3 Theory: The USILang Parser

## Q1 - Top-Down vs. Bottom-Up

Top-down parsing (recursive descent) builds the parse tree starting from the grammar's start symbol and works downward, predicting which rule applies and expanding non-terminals until it reaches terminals that match the input. Bottom-up parsing works the opposite direction: it starts from the raw token stream and repeatedly reduces recognized sequences of terminals/non-terminals into higher-level non-terminals, building upward until everything collapses into the start symbol.

Recursive descent works perfectly for a single-developer project like USILang because its structure maps one-to-one onto the grammar: each non-terminal becomes exactly one function, so the code's call structure IS the grammar's structure. That means the source is self-documenting (`parse_expr` calls `parse_term` calls `parse_factor` reads exactly like `<expr> -> <term> -> <factor>`), and when something goes wrong, the Python call stack at the crash site *is* the parse-tree path down to the failure, which makes hand-debugging fast without any generated tables or parser-generator tooling to fight. Bottom-up/LR parsing is strictly more powerful in the formal sense (it accepts a larger class of grammars, including left-recursive ones, without rewriting), but that power comes from state tables that are normally produced by a generator (yacc/bison) rather than written and read by hand -- exactly the wrong tradeoff for a course project meant to teach the grammar itself.

The one category recursive descent cannot handle without modification is **left-recursive rules** -- the same shape rejected in PA 1, Question 1 (`<expr> ::= <expr> '+' <term> | <term>`). Translated directly into a function, `parse_expr` would call itself before consuming any token, causing unbounded recursion (a stack overflow) rather than a parse error. This is why PA 1's grammar was rewritten into the right-recursion-free, iterative form `<expr> ::= <term> { '+' <term> }`, which `parse_expr` implements below with a `while` loop instead of self-recursion.

## Q2 - AST and Call-Stack Tracing

Input: `x = 2 + 3 * 4;`

**AST** (precedence encoded structurally -- `*` nested one level deeper than `+` because it binds tighter):

```
Assignment("x")
       |
     BinOp("+")
     /        \
Number(2)   BinOp("*")
             /       \
        Number(3)   Number(4)
```

`Assignment(name="x", expr=BinOp("+", Number(2), BinOp("*", Number(3), Number(4))))`

**Call-stack trace**, in invocation order, down through the first `NUMBER` token consumed:

1. `parse_statement` -- peeks the current token (`IDENT "x"`); since it is not `LET`, dispatches to `parse_assignment` without consuming anything yet.
2. `parse_assignment` -- consumes `IDENT("x")`, then consumes `ASSIGN("=")`, then calls `parse_expr` to parse the right-hand side.
3. `parse_expr` -- immediately calls `parse_term` (it must have a term before it can even check for a trailing `+`/`-`).
4. `parse_term` -- immediately calls `parse_factor` (same reasoning, one level down: it needs a factor before checking for `*`/`/`).
5. `parse_factor` -- peeks the current token, sees `NUMBER("2")`, and **consumes it**, returning `Number(2)`.

Control now unwinds: `parse_term` peeks `PLUS`, which is not `*`/`/`, so its loop never runs and it returns `Number(2)` unchanged. `parse_expr` peeks `PLUS`, consumes it, and calls `parse_term` again -- which calls `parse_factor` again to consume `NUMBER("3")`, then (inside that same `parse_term` call) sees `STAR`, consumes it, calls `parse_factor` once more to consume `NUMBER("4")`, and folds `BinOp("*", Number(3), Number(4))` *before* ever returning to `parse_expr`. `parse_expr` then folds `BinOp("+", Number(2), BinOp("*", Number(3), Number(4)))` and returns it up to `parse_assignment`, which wraps it in `Assignment("x", ...)`. The `*` ends up nested below the `+` purely because `parse_term`'s loop finishes before control returns to `parse_expr` -- precedence is a side effect of the call layering, not a table.

## Q3 - Error Recovery Design

Scenario: `parse_factor` has consumed `LPAREN`, called `parse_expr` to parse the inner expression (e.g., `2 + 3`), and now calls `state.expect("RPAREN")` -- but the next token is `SEMI` (input was `(2 + 3;`).

The raised error should be a `ParseError` with a message of the form:

> `Line 1: expected RPAREN, found SEMI (';').`

Beyond the bare "something went wrong" text, the message must always include two pieces of information:

1. **The line number** where the mismatch occurred, so the programmer can jump straight to the offending line in their source file instead of re-scanning the whole program.
2. **What was expected versus what was actually found** (the expected token type, and the actual token's type *and* lexeme) -- without the contrast, an error that just says "found SEMI" gives no hint about what the parser was trying to do at that point (close a paren, end a statement, etc.), and the programmer has no way to know what to change it to.

This is exactly what `_ParserState.expect()` already produces, and it is why `parse_factor` must call `state.expect("RPAREN")` after `parse_expr` returns rather than trusting that the next token is correct.

## Q4 - Syntactic vs. Semantic Responsibility

`let x = 5;` and `x = 5;` must produce two different AST node types, `Declaration` and `Assignment`, even though the parser itself has no idea at this point whether `x` was already declared -- that check is semantic (it requires knowing what has been declared so far) and syntactic (it is signaled purely by the presence or absence of the `let` keyword, a fact available immediately from one token of lookahead, with zero semantic analysis required).

This distinction has to be made **now, at the syntax level**, because syntax is the only stage where the literal textual difference between the two forms is still visible. By the time the AST reaches PA 4, all that survives is whatever the node types encode; if the parser throws away the `let`-vs-no-`let` distinction and collapses both into one generic `Statement` node, that information is gone forever and cannot be recovered downstream.

If PA 4's symbol table walker only saw a generic `Statement` node, it would have no way to tell "define a new binding" from "mutate an existing one" -- which is the entire job of a symbol table pass. It could not detect **redeclaration** (`let x = 1; let x = 2;` should be an error, but a generic walker has no signal that either occurrence was a `let` at all) or **use-before-declaration** (`x = 5;` where `x` was never declared should be an error, but nothing distinguishes that from a legitimate re-assignment to an already-declared `x`). Keeping `Declaration` and `Assignment` as distinct node types costs nothing in the parser (it is simply which function was called, driven by one token of lookahead) and is the only way PA 4 can do its job at all.