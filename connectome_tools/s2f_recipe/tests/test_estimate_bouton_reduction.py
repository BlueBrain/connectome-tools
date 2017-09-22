import os
import numpy as np
import nose.tools as nt

from mock import Mock

import connectome_tools.s2f_recipe.estimate_bouton_reduction as test_module


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_1():
    circuit = Mock()
    circuit.v2.stats.sample_bouton_density.return_value = np.array([1., 3.])
    expected = {
        ('*', '*'): {
            'bouton_reduction_factor': 5.0
        }
    }
    actual = test_module.execute(circuit, bio_data=10.0)
    nt.assert_equal(actual, expected)


def test_2():
    circuit = Mock()
    circuit.v2.cells.mtypes = ['L1_DAC', 'L23_MC', 'L5_TPC']
    circuit.v2.stats.sample_bouton_density.return_value = np.array([1., 3.])
    expected = {
        ('*', '*'): {
            'bouton_reduction_factor': 21.0
        }
    }
    actual = test_module.execute(circuit, bio_data=os.path.join(TEST_DATA_DIR, "bouton_density.tsv"))
    nt.assert_equal(actual, expected)
