from itertools import chain

from bluepysnap.edges import EdgePopulation
from mock import MagicMock

import connectome_tools.s2f_recipe.generalized_cv as test_module


def test_prepare():
    cv = 0.32
    expected = {("*", "*"): {"cv_syns_connection": cv}}
    population = MagicMock(EdgePopulation)

    task_generator = test_module.Executor().prepare(population, cv)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected
