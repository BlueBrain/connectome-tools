import numpy as np
import numpy.testing as npt
import pytest

from connectome_tools import equation as test_module


@pytest.mark.parametrize(
    ("expression", "context", "expected"),
    [
        ("1 + 2 * 3", None, 7),
        ("1 + 2 * n", {"n": 3}, 7),
        ("sin(n * pi)", {"n": 0.5}, 1.0),
        ("n * 3", {"n": np.nan}, np.nan),
        ("1 / n", {"n": np.nan}, np.nan),
    ],
)
def test_evaluate(expression, context, expected):
    actual = test_module.evaluate(expression, context)
    npt.assert_almost_equal(actual, expected)


@pytest.mark.parametrize(
    ("expression", "error", "match"),
    [
        ("1 + 2 *", SyntaxError, "invalid syntax"),
        ("sqrt(-1)", ValueError, "math domain error"),
        ("1 / 0", ValueError, "math domain error"),
        ("sum([1, 2])", NameError, "The use of 'sum' is not allowed"),
        ("open('/etc/passwd')", NameError, "The use of 'open' is not allowed"),
        (
            "().__class__.__base__.__subclasses__()",
            NameError,
            "The use of '__class__' is not allowed",
        ),
    ],
)
def test_evaluate_raises(expression, error, match):
    with pytest.raises(error, match=match):
        test_module.evaluate(expression)