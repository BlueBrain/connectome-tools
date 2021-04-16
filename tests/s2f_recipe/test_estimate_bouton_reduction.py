import os
from itertools import chain

import numpy as np
import numpy.testing as npt
from bluepy import Circuit
from mock import MagicMock, patch

import connectome_tools.s2f_recipe.estimate_bouton_reduction as test_module

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")


@patch(test_module.__name__ + ".sample_bouton_density", return_value=np.array([1.0, 3.0]))
def test_1(_):
    circuit = MagicMock(Circuit)
    circuit.config = {}
    expected = {("*", "*"): {"bouton_reduction_factor": 5.0}}
    task_generator = test_module.Executor().prepare(circuit, bio_data=10.0)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    npt.assert_equal(actual, expected)


@patch(test_module.__name__ + ".sample_bouton_density", return_value=np.array([1.0, 3.0]))
def test_2(_):
    circuit = MagicMock(Circuit)
    circuit.config = {}
    expected = {("*", "*"): {"bouton_reduction_factor": 21.0}}
    bio_data = os.path.join(TEST_DATA_DIR, "bouton_density.tsv")
    task_generator = test_module.Executor().prepare(circuit, bio_data=bio_data)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    npt.assert_equal(actual, expected)
