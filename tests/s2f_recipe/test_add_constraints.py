from itertools import chain

from bluepy import Circuit
from mock import MagicMock

import connectome_tools.s2f_recipe.add_constraints as test_module


def test_prepare():
    constraints = {"fromRegion": "SSp-ll@right"}
    expected = {("*", "*"): constraints}
    circuit = MagicMock(Circuit)

    task_generator = test_module.Executor().prepare(circuit, **constraints)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected
