#!/usr/bin/env python3
"""Simple calculator: add, subtract, multiply, divide two numbers (Notion MCP Challenge)."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


def parse_number(raw: str) -> float:
    s = raw.strip()
    if not s:
        raise ValueError("Enter a number in both fields.")
    return float(s)


def compute(a: float, b: float, op: str) -> float:
    if op == "+":
        return a + b
    if op == "−":
        return a - b
    if op == "×":
        return a * b
    if op == "÷":
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return a / b
    raise ValueError("Unknown operation.")


class CalculatorApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=16)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        title = ttk.Label(self, text="Calculator", font=tkfont.Font(size=16, weight="bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        ttk.Label(self, text="First number:").grid(row=1, column=0, sticky="w", pady=4)
        self.entry_a = ttk.Entry(self, width=22)
        self.entry_a.grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)

        ttk.Label(self, text="Second number:").grid(row=2, column=0, sticky="w", pady=4)
        self.entry_b = ttk.Entry(self, width=22)
        self.entry_b.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)

        ttk.Label(self, text="Operation:").grid(row=3, column=0, sticky="w", pady=8)
        self.op = tk.StringVar(value="+")
        ops = ("+", "−", "×", "÷")
        op_frame = ttk.Frame(self)
        op_frame.grid(row=3, column=1, columnspan=2, sticky="w", pady=8)
        for i, symbol in enumerate(ops):
            ttk.Radiobutton(op_frame, text=symbol, variable=self.op, value=symbol).grid(
                row=0, column=i, padx=(0, 8)
            )

        self.calc_btn = ttk.Button(self, text="Calculate", command=self.on_calculate)
        self.calc_btn.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(8, 6))

        ttk.Label(self, text="Result:").grid(row=5, column=0, sticky="nw", pady=4)
        self.result = tk.Text(self, height=3, width=32, wrap="word", state="disabled", relief="flat")
        self.result.grid(row=5, column=1, columnspan=2, sticky="ew", pady=4)

        ttk.Label(self, text="Decimals and negatives are supported.", foreground="gray").grid(
            row=6, column=0, columnspan=3, sticky="w", pady=(12, 0)
        )

        self.entry_a.bind("<Return>", lambda e: self.on_calculate())
        self.entry_b.bind("<Return>", lambda e: self.on_calculate())

    def set_result(self, message: str, *, is_error: bool) -> None:
        self.result.configure(state="normal")
        self.result.delete("1.0", tk.END)
        self.result.insert(tk.END, message)
        self.result.tag_remove("err", "1.0", tk.END)
        if is_error:
            self.result.tag_add("err", "1.0", tk.END)
            self.result.tag_config("err", foreground="#b00020")
        else:
            self.result.tag_config("err", foreground="")
        self.result.configure(state="disabled")

    def on_calculate(self) -> None:
        try:
            a = parse_number(self.entry_a.get())
            b = parse_number(self.entry_b.get())
            value = compute(a, b, self.op.get())
            if value == int(value) and abs(value) < 1e15:
                text = f"{int(value)}"
            else:
                text = f"{value:.12g}"
            self.set_result(text, is_error=False)
        except ValueError as e:
            self.set_result(str(e), is_error=True)
        except ZeroDivisionError as e:
            self.set_result(str(e), is_error=True)


def main() -> None:
    root = tk.Tk()
    root.title("Calculator App")
    root.minsize(360, 280)
    root.geometry("400x320")
    style = ttk.Style()
    if "clam" in style.theme_names():
        style.theme_use("clam")
    CalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
