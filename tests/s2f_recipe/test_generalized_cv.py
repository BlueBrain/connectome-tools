from itertools import chain

from bluepy.v2 import Circuit
from mock import MagicMock

import connectome_tools.s2f_recipe.generalized_cv as test_module


def test_prepare():
    cv = 0.32
    expected = {("*", "*"): {"cv_syns_connection": cv}}
    circuit = MagicMock(Circuit)

    task_generator = test_module.prepare(circuit, cv)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected
