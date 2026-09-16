"""
PA 3: The USILang Parser -- verification suite.

Run: python test_parser.py
Prints the Success Token only if every check below passes.
"""

import base64
import hashlib
import sys

from lexer import tokenize
from parser import (Assignment, BinOp, Declaration, Number, ParseError,
                     Program, Variable, parse)

ASSIGNMENT_ID = "PA03"


def get_student_id() -> str:
    """Prompt for the student's USI username; baked into the Success Token
    so a copied/shared token decodes to someone else's name, not yours."""
    student_id = input("Enter your USI username (e.g. cwill): ").strip()
    while not student_id:
        student_id = input("Username cannot be blank. Enter your USI username: ").strip()
    return student_id


def generate_token(assignment_id: str, student_id: str) -> str:
    digest = hashlib.sha256(f"CS379-{assignment_id}-{student_id}-VERIFIED".encode()).hexdigest()[:16]
    raw = f"CS379|{assignment_id}|{student_id}|PASS|{digest}"
    return base64.b64encode(raw.encode()).decode()


def print_success_banner(assignment_id: str) -> None:
    student_id = get_student_id()
    token = generate_token(assignment_id, student_id)
    print("\n" + "=" * 60)
    print(f"  ALL CHECKS PASSED -- {assignment_id}")
    print(f"  STUDENT: {student_id}")
    print("  SUCCESS TOKEN (paste this into Blackboard):")
    print(f"  {token}")
    print("=" * 60 + "\n")


def check(label: str, condition: bool, failures: list) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        failures.append(label)


def ast_equal(a, b) -> bool:
    """Structural equality that ignores `line` fields (only shape/values matter here)."""
    if type(a) is not type(b):
        return False
    if isinstance(a, Program):
        return len(a.statements) == len(b.statements) and all(ast_equal(x, y) for x, y in zip(a.statements, b.statements))
    if isinstance(a, (Declaration, Assignment)):
        return a.name == b.name and ast_equal(a.expr, b.expr)
    if isinstance(a, BinOp):
        return a.op == b.op and ast_equal(a.left, b.left) and ast_equal(a.right, b.right)
    if isinstance(a, Number):
        return a.value == b.value
    if isinstance(a, Variable):
        return a.name == b.name
    return a == b


def parse_source(source: str):
    return parse(tokenize(source))


def main() -> int:
    failures: list = []

    print("Testing valid programs against expected AST shapes...\n")

    # From Part A, Question 2: x = 2 + 3 * 4;  ->  Assignment(x, BinOp(+, 2, BinOp(*, 3, 4)))
    ast1 = parse_source("x = 2 + 3 * 4;")
    expected1 = Program([Assignment("x", BinOp("+", Number(2, 0), BinOp("*", Number(3, 0), Number(4, 0), 0), 0), 0)])
    check("'x = 2 + 3 * 4;' parses with * nested deeper than + (correct precedence)", ast_equal(ast1, expected1), failures)

    # Left-associativity: 1 - 2 - 3  ->  ((1 - 2) - 3), NOT (1 - (2 - 3))
    ast2 = parse_source("let x = 1 - 2 - 3;")
    expected2 = Program([Declaration("x", BinOp("-", BinOp("-", Number(1, 0), Number(2, 0), 0), Number(3, 0), 0), 0)])
    check("'1 - 2 - 3' is left-associative: ((1 - 2) - 3)", ast_equal(ast2, expected2), failures)

    # Parenthesized grouping, arbitrary nesting
    ast3 = parse_source("let x = ((((1))));")
    expected3 = Program([Declaration("x", Number(1, 0), 0)])
    check("deeply nested parens collapse to the inner value", ast_equal(ast3, expected3), failures)

    # Multi-statement program, declaration + assignment + variable reference
    ast4 = parse_source("let a = 1;\nlet b = 2;\na = a + b * 3;")
    expected4 = Program([
        Declaration("a", Number(1, 0), 0),
        Declaration("b", Number(2, 0), 0),
        Assignment("a", BinOp("+", Variable("a", 0), BinOp("*", Variable("b", 0), Number(3, 0), 0), 0), 0),
    ])
    check("multi-statement program produces 3 correctly-typed top-level statements", ast_equal(ast4, expected4), failures)

    print("\nTesting invalid programs raise ParseError...\n")
    invalid_cases = [
        "(2 + 3;",       # missing RPAREN -- Part A, Question 3
        "let = 5;",
        "x 5;",
        "let x = 5",     # missing semicolon
        "let x = ;",
    ]
    for source in invalid_cases:
        try:
            parse_source(source)
            check(f"'{source}' raises ParseError", False, failures)
        except ParseError:
            check(f"'{source}' raises ParseError", True, failures)

    print()
    if failures:
        print(f"{len(failures)} check(s) failed. No token issued.")
        return 1

    print_success_banner(ASSIGNMENT_ID)
    return 0


if __name__ == "__main__":
    sys.exit(main())
