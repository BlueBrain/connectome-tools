import os
import numpy as np
import nose.tools as nt

from mock import Mock

import connectome_tools.s2f_recipe.estimate_individual_bouton_reduction as test_module


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def mock_sample_bouton_density(**kwargs):
    mtype = kwargs['group']['mtype']
    return {
        'L1_DAC': np.empty(0),
        'L23_MC': np.array([1.0, 3.0]),
        'L5_TPC': np.array([0.5, 1.5]),
    }[mtype]


def test_1():
    circuit = Mock()
    circuit.v2.cells.mtypes = ['L1_DAC', 'L23_MC', 'L5_TPC']
    circuit.v2.stats.sample_bouton_density = mock_sample_bouton_density
    expected = {
        ('L23_MC', '*'): {'bouton_reduction_factor': 5.0},
        ('L5_TPC', '*'): {'bouton_reduction_factor': 10.0},
    }
    actual = test_module.execute(circuit, bio_data=10.0)
    nt.assert_equal(actual, expected)


def test_2():
    circuit = Mock()
    circuit.v2.cells.mtypes = ['L1_DAC', 'L23_MC', 'L5_TPC']
    circuit.v2.stats.sample_bouton_density = mock_sample_bouton_density
    expected = {
        ('L23_MC', '*'): {'bouton_reduction_factor': 15.0},
    }
    actual = test_module.execute(circuit, bio_data=os.path.join(TEST_DATA_DIR, "bouton_density.tsv"))
    nt.assert_equal(actual, expected)
