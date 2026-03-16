import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import ast


# A built-in dataset. If the user's question "matches" a topic,
# we answer locally. There is NO online call anymore.
TOPICS = [
    {
        "topic": "Photosynthesis (Science)",
        "keywords": ["photosynthesis", "chlorophyll", "plants make food", "sunlight"],
        "answer": (
            "Photosynthesis is the process plants use to convert sunlight into chemical energy. "
            "Using chlorophyll, plants take in carbon dioxide (CO₂) and water (H₂O) and produce "
            "glucose (sugar) and oxygen (O₂)."
        ),
    },
    {
        "topic": "Newton's Second Law (Physics)",
        "keywords": ["newton", "second law", "force equals", "f=ma", "acceleration"],
        "answer": "Newton's Second Law states that force equals mass times acceleration: F = m × a.",
    },
    {
        "topic": "Pythagorean Theorem (Math)",
        "keywords": ["pythagorean", "right triangle", "a^2+b^2", "c^2"],
        "answer": (
            "In a right triangle, the Pythagorean Theorem is a² + b² = c², "
            "where c is the hypotenuse."
        ),
    },
    {
        "topic": "Prime Numbers (Math)",
        "keywords": ["prime number", "prime", "divisible by", "factors"],
        "answer": (
            "A prime number is an integer greater than 1 with exactly two positive divisors: 1 and itself "
            "(e.g., 2, 3, 5, 7, 11)."
        ),
    },
    {
        "topic": "States of Matter (Science)",
        "keywords": ["states of matter", "solid", "liquid", "gas", "plasma"],
        "answer": (
            "Common states of matter include solid, liquid, gas, and plasma. "
            "They differ by how particles are arranged and how freely they move."
        ),
    },
    {
        "topic": "Reverse a list in Python",
        "keywords": ["python", "reverse list", "list reverse", "list[::-1]", ".reverse()"],
        "answer": (
            "In Python you can reverse a list in two common ways:\n"
            "1) In-place (modifies the list):\n"
            "   my_list.reverse()\n\n"
            "2) Create a reversed copy using slicing:\n"
            "   reversed_list = my_list[::-1]"
        ),
    },
    {
        "topic": "Python list comprehension (squares)",
        "keywords": ["python", "list comprehension", "squares", "square numbers"],
        "answer": (
            "A list comprehension lets you build a list in one line. For example, "
            "to create the squares of 0–9:\n"
            "squares = [i * i for i in range(10)]"
        ),
    },
    {
        "topic": "While loop in Python",
        "keywords": ["python", "while loop", "loop until", "while condition"],
        "answer": (
            "A simple while loop in Python looks like:\n"
            "count = 0\n"
            "while count < 5:\n"
            "    print(count)\n"
            "    count += 1"
        ),
    },
    {
        "topic": "Slope of a line (Math)",
        "keywords": ["slope", "line", "two points", "y2-y1", "x2-x1"],
        "answer": (
            "Given two points (x₁, y₁) and (x₂, y₂), the slope m is:\n"
            "m = (y₂ - y₁) / (x₂ - x₁)"
        ),
    },
    {
        "topic": "Quadratic formula (Math)",
        "keywords": ["quadratic", "quadratic formula", "ax^2+bx+c", "roots of quadratic"],
        "answer": (
            "For ax² + bx + c = 0, the roots are:\n"
            "x = (-b ± √(b² - 4ac)) / (2a)"
        ),
    },
]


def normalize(text: str) -> str:
    """Normalize user input for simple keyword matching."""
    return " ".join(text.lower().strip().split())


def _safe_eval_arithmetic(expr: str) -> str | None:
    """
    Evaluate simple arithmetic safely.

    Supported:
      - integers / decimals
      - +, -, *, /, //, %, **, parentheses

    Not supported:
      - names (variables), function calls, attribute access, indexing, etc.
    """
    raw = expr.strip()
    if not raw:
        return None

    # Quick filter: only allow characters commonly used in arithmetic expressions.
    allowed_chars = set("0123456789.+-*/()%() \t\r\n")
    if any(ch not in allowed_chars for ch in raw):
        return None

    try:
        node = ast.parse(raw, mode="eval")
    except SyntaxError:
        return None

    def eval_node(n: ast.AST):
        if isinstance(n, ast.Expression):
            return eval_node(n.body)

        # Numbers (py3.8+ uses Constant)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value

        # Unary ops: +x, -x
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            v = eval_node(n.operand)
            return +v if isinstance(n.op, ast.UAdd) else -v

        # Binary ops
        if isinstance(n, ast.BinOp) and isinstance(
            n.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow)
        ):
            left = eval_node(n.left)
            right = eval_node(n.right)
            op = n.op
            if isinstance(op, ast.Add):
                return left + right
            if isinstance(op, ast.Sub):
                return left - right
            if isinstance(op, ast.Mult):
                return left * right
            if isinstance(op, ast.Div):
                return left / right
            if isinstance(op, ast.FloorDiv):
                return left // right
            if isinstance(op, ast.Mod):
                return left % right
            if isinstance(op, ast.Pow):
                return left ** right

        raise ValueError("Unsupported expression")

    try:
        result = eval_node(node)
    except Exception:
        return None

    return f"[Math]\n{raw} = {result}"


def dataset_answer(question: str) -> str | None:
    """
    If the question matches a topic (by simple keyword containment),
    return the dataset answer. Otherwise return None.
    """
    # If it's simple arithmetic like "56*56", answer locally (avoid irrelevant web results).
    arithmetic = _safe_eval_arithmetic(question)
    if arithmetic is not None:
        return arithmetic

    q = normalize(question)
    if not q:
        return None

    best = None
    best_score = 0
    for item in TOPICS:
        score = sum(1 for kw in item["keywords"] if kw in q)
        if score > best_score:
            best_score = score
            best = item

    # Require at least one keyword hit to count as a match.
    if best and best_score > 0:
        return f"[Dataset: {best['topic']}]\n{best['answer']}"
    return None


class QAApp(ttk.Frame):
    """A simple Tkinter Q&A app with a built-in math + code dataset (offline only)."""

    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=12)
        self.master = master

        self.question_var = tk.StringVar()

        self._build_ui()
        self._configure_layout()

    def _build_ui(self) -> None:
        self.title_label = ttk.Label(self, text="Q&A Assistant", font=("Segoe UI", 14, "bold"))
        self.subtitle_label = ttk.Label(
            self,
            text="Ask a math or Python question. If it matches a built-in topic, you'll get an instant answer.",
            wraplength=640,
        )

        self.question_entry = ttk.Entry(self, textvariable=self.question_var)
        self.ask_button = ttk.Button(self, text="Ask", command=self.on_ask)

        self.answer_box = ScrolledText(self, wrap="word", height=16)
        self.answer_box.configure(state="disabled", font=("Segoe UI", 10))

        self.hint_label = ttk.Label(
            self,
            text="Tip: Try “56*56”, “What is the Pythagorean theorem?” or “How do I reverse a list in Python?”.",
            foreground="#555555",
        )

        self.title_label.grid(row=0, column=0, columnspan=2, sticky="w")
        self.subtitle_label.grid(row=1, column=0, columnspan=2, sticky="we", pady=(2, 10))
        self.question_entry.grid(row=2, column=0, sticky="we")
        self.ask_button.grid(row=2, column=1, sticky="e", padx=(10, 0))
        self.answer_box.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(10, 6))
        self.hint_label.grid(row=4, column=0, columnspan=2, sticky="w")

        # Let the user press Enter to ask.
        self.question_entry.bind("<Return>", lambda _evt: self.on_ask())
        self.question_entry.focus_set()

    def _configure_layout(self) -> None:
        self.grid(row=0, column=0, sticky="nsew")
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(3, weight=1)

    def _set_answer(self, text: str) -> None:
        self.answer_box.configure(state="normal")
        self.answer_box.delete("1.0", "end")
        self.answer_box.insert("1.0", text.strip() + "\n")
        self.answer_box.configure(state="disabled")

    def on_ask(self) -> None:
        question = self.question_var.get().strip()
        if not question:
            self._set_answer("Please type a question first.")
            return

        # First try the local dataset.
        local = dataset_answer(question)
        if local is not None:
            self._set_answer(local)
            return
        # No online dataset: just say it's unknown.
        self._set_answer("I don't have that in my built-in dataset yet.")


def main() -> None:
    root = tk.Tk()
    root.title("Tkinter Q&A Assistant")
    root.minsize(720, 420)

    # Use ttk's default theme and a tiny bit of padding for a clean look.
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    QAApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
