#!/usr/bin/env python3
"""Simple calculator: add, subtract, multiply, divide two numbers.

Spec from Notion page "Calculator App":
- Input validation for numbers
- Division by zero handled gracefully
- Clear result display
- Decimal numbers supported
"""

from __future__ import annotations

import re
import sys
from decimal import Decimal, InvalidOperation


def parse_number(raw: str) -> Decimal:
    s = raw.strip()
    if not s:
        raise ValueError("Empty input is not a number.")
    # Allow optional leading +/- and decimal point
    if not re.fullmatch(r"[+-]?(\d+\.?\d*|\.\d+)", s):
        raise ValueError(f"Not a valid number: {raw!r}")
    try:
        return Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f"Not a valid number: {raw!r}") from exc


def calculate(a: Decimal, op: str, b: Decimal) -> Decimal:
    if op == "+":
        return a + b
    if op == "-":
        return a - b
    if op == "*":
        return a * b
    if op == "/":
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return a / b
    raise ValueError(f"Unknown operation: {op!r}")


def format_result(value: Decimal) -> str:
    s = format(value.normalize(), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s if s else "0"


def run_interactive() -> None:
    print("Simple calculator — enter two numbers and an operator (+ - * /).")
    print("Type 'q' to quit.\n")
    while True:
        try:
            first = input("First number: ").strip()
            if first.lower() == "q":
                return
            a = parse_number(first)

            op_raw = input("Operator (+ - * /): ").strip().lower()
            if op_raw == "q":
                return
            if op_raw in ("x",):
                op_raw = "*"
            if op_raw not in "+-*/":
                print("Error: use one of + - * /\n")
                continue

            second = input("Second number: ").strip()
            if second.lower() == "q":
                return
            b = parse_number(second)

            try:
                result = calculate(a, op_raw, b)
            except ZeroDivisionError as e:
                print(f"\n{e}\n")
                continue

            op_symbol = op_raw if op_raw != "*" else "×"
            print(
                f"\n  {format_result(a)} {op_symbol} {format_result(b)} = {format_result(result)}\n"
            )
        except ValueError as e:
            print(f"\nError: {e}\n")
        except (EOFError, KeyboardInterrupt):
            print()
            return


def run_cli(argv: list[str]) -> int:
    """Usage: calculator_app.py <a> <op> <b>   e.g. 3.5 + 2"""
    if len(argv) != 4:
        print("Usage: python calculator_app.py <number> <+|-|*|x|/> <number>", file=sys.stderr)
        return 2
    _, a_s, op_s, b_s = argv
    try:
        a, b = parse_number(a_s), parse_number(b_s)
        op_norm = op_s.strip().lower()
        if op_norm == "x":
            op_norm = "*"
        if op_norm not in "+-*/":
            print("Operator must be +, -, *, /, or x", file=sys.stderr)
            return 2
        result = calculate(a, op_norm, b)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except ZeroDivisionError as e:
        print(str(e), file=sys.stderr)
        return 1
    op_symbol = op_norm if op_norm != "*" else "×"
    print(f"{format_result(a)} {op_symbol} {format_result(b)} = {format_result(result)}")
    return 0


def main() -> None:
    if len(sys.argv) == 4:
        raise SystemExit(run_cli(sys.argv))
    if len(sys.argv) == 1:
        run_interactive()
        return
    print("Run with no arguments for interactive mode, or: python calculator_app.py <a> <op> <b>", file=sys.stderr)
    raise SystemExit(2)


if __name__ == "__main__":
    main()
