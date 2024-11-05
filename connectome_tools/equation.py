"""Math expression evaluator using Python's eval() and math.

Based on https://realpython.com/python-eval-function/#building-a-math-expressions-evaluator
"""

import math

ALLOWED_NAMES = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}


def evaluate(expression, context=None):
    """Evaluate a math expression.

    Args:
        expression(str): math expression.
        context: optional dict of variables.

    Examples:
        >>> evaluate("1 + 2 * 3")
        7
        >>> evaluate("1 + 2 * n", context={"n": 3})
        7
        >>> evaluate("sin(n * pi)", context={"n": 0.5})
        1.0
    """
    allowed_names = {**ALLOWED_NAMES, **(context or {})}
    code = compile(expression, "<string>", "eval")
    for name in code.co_names:
        if name not in allowed_names:
            raise NameError(f"The use of '{name}' is not allowed")
    return eval(code, {"__builtins__": {}}, allowed_names)
