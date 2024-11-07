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

    Returns:
        the calculated value.

    Raises:
        NameError: if an unexpected name is present in the given expression.

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
    # Add `__import__` to the `__builtins__` dict, because numpy may print a RuntimeWarning,
    # and this causes `__import__('warnings')` to be explicitly called in Python >= 3.13,
    # raising the exception KeyError: '__import__' if __import__ is not found in globals.
    # For example, the following instruction raises with numpy 2.1.3 and Python 3.13.0:
    # >>> eval('n ** 0.5', {'__builtins__': {}}, {'n': np.float64(-1)})
    return eval(  # pylint: disable=eval-used
        code, {"__builtins__": {"__import__": __import__}}, allowed_names
    )
