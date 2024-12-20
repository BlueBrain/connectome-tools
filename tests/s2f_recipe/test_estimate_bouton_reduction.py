import os
from itertools import chain

import numpy as np
import numpy.testing as npt
from bluepysnap.edges import EdgePopulation
from mock import MagicMock, patch
from utils import TEST_DATA_DIR

import connectome_tools.s2f_recipe.estimate_bouton_reduction as test_module


@patch(test_module.__name__ + ".sample_bouton_density", return_value=np.array([1.0, 3.0]))
def test_1(_):
    population = MagicMock(EdgePopulation)
    expected = {("*", "*"): {"bouton_reduction_factor": 5.0}}
    task_generator = test_module.Executor().prepare(population, bio_data=10.0, atlas_path="Foo")
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    npt.assert_equal(actual, expected)


@patch(test_module.__name__ + ".sample_bouton_density", return_value=np.array([1.0, 3.0]))
def test_2(_):
    population = MagicMock(EdgePopulation)
    expected = {("*", "*"): {"bouton_reduction_factor": 21.0}}
    bio_data = os.path.join(TEST_DATA_DIR, "bouton_density.tsv")
    task_generator = test_module.Executor().prepare(population, bio_data=bio_data, atlas_path="Foo")
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    npt.assert_equal(actual, expected)
