import os
from itertools import chain

import numpy as np
import numpy.testing as npt
from bluepy.v2 import Circuit
from mock import patch, MagicMock

import connectome_tools.s2f_recipe.estimate_bouton_reduction as test_module

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")


@patch(test_module.__name__ + '.sample_bouton_density', return_value=np.array([1., 3.]))
def test_1(_):
    circuit = MagicMock(Circuit)
    expected = {
        ('*', '*'): {
            'bouton_reduction_factor': 5.0
        }
    }
    worker_generator = test_module.prepare(circuit, bio_data=10.0)
    result_generator = (worker() for worker in worker_generator)
    actual = dict(chain.from_iterable(result_generator))

    npt.assert_equal(actual, expected)


@patch(test_module.__name__ + '.sample_bouton_density', return_value=np.array([1., 3.]))
def test_2(_):
    circuit = MagicMock(Circuit)
    expected = {
        ('*', '*'): {
            'bouton_reduction_factor': 21.0
        }
    }
    bio_data = os.path.join(TEST_DATA_DIR, "bouton_density.tsv")
    worker_generator = test_module.prepare(circuit, bio_data=bio_data)
    result_generator = (worker() for worker in worker_generator)
    actual = dict(chain.from_iterable(result_generator))

    npt.assert_equal(actual, expected)
