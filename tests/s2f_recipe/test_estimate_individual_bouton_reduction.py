import os
from itertools import chain

import numpy as np
import numpy.testing as npt
from bluepysnap.edges import EdgePopulation
from mock import MagicMock, patch
from utils import TEST_DATA_DIR

import connectome_tools.s2f_recipe.estimate_individual_bouton_reduction as test_module


def mock_sample_bouton_density(population, **kwargs):
    mtype = kwargs["group"]["mtype"]
    samples = {
        "L1_DAC": np.empty(0),
        "L23_MC": np.array([1.0, 3.0]),
        "L5_TPC": np.array([0.5, 1.5]),
    }
    return samples[mtype]


@patch.object(test_module, "sample_bouton_density", side_effect=mock_sample_bouton_density)
@patch.object(test_module, "get_mtypes_from_edge_population")
def test_1(mock_get_mtypes, _):
    population = MagicMock(EdgePopulation)
    mock_get_mtypes.return_value = ["L1_DAC", "L23_MC", "L5_TPC"]
    expected = {
        ("L23_MC", "*"): {"bouton_reduction_factor": 5.0},
        ("L5_TPC", "*"): {"bouton_reduction_factor": 10.0},
    }
    task_generator = test_module.Executor().prepare(population, bio_data=10.0)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    npt.assert_equal(actual, expected)


@patch.object(test_module, "sample_bouton_density", side_effect=mock_sample_bouton_density)
@patch.object(test_module, "get_mtypes_from_edge_population")
def test_2(mock_get_mtypes, _):
    population = MagicMock(EdgePopulation)
    mock_get_mtypes.return_value = ["L1_DAC", "L23_MC", "L5_TPC"]
    expected = {
        ("L23_MC", "*"): {"bouton_reduction_factor": 15.0},
    }
    bio_data = os.path.join(TEST_DATA_DIR, "bouton_density.tsv")
    task_generator = test_module.Executor().prepare(population, bio_data=bio_data)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    npt.assert_equal(actual, expected)
