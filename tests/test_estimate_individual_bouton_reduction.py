import os

import numpy as np
import numpy.testing as npt
from mock import Mock, patch

import connectome_tools.s2f_recipe.estimate_individual_bouton_reduction as test_module

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def mock_sample_bouton_density(circuit, **kwargs):
    mtype = kwargs['group']['mtype']
    return {
        'L1_DAC': np.empty(0),
        'L23_MC': np.array([1.0, 3.0]),
        'L5_TPC': np.array([0.5, 1.5]),
    }[mtype]


@patch(test_module.__name__ + '.sample_bouton_density', side_effect=mock_sample_bouton_density)
def test_1(_):
    circuit = Mock()
    circuit.cells.mtypes = ['L1_DAC', 'L23_MC', 'L5_TPC']
    expected = {
        ('L23_MC', '*'): {'bouton_reduction_factor': 5.0},
        ('L5_TPC', '*'): {'bouton_reduction_factor': 10.0},
    }
    actual = test_module.execute(circuit, bio_data=10.0)
    npt.assert_equal(actual, expected)


@patch(test_module.__name__ + '.sample_bouton_density', side_effect=mock_sample_bouton_density)
def test_2(_):
    circuit = Mock()
    circuit.cells.mtypes = ['L1_DAC', 'L23_MC', 'L5_TPC']
    expected = {
        ('L23_MC', '*'): {'bouton_reduction_factor': 15.0},
    }
    actual = test_module.execute(circuit, bio_data=os.path.join(TEST_DATA_DIR, "bouton_density.tsv"))
    npt.assert_equal(actual, expected)
