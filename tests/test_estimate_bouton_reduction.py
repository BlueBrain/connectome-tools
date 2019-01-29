import os
import numpy as np
import nose.tools as nt

from mock import Mock, patch

import connectome_tools.stats
import connectome_tools.s2f_recipe.estimate_bouton_reduction as test_module


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@patch(test_module.__name__ + '.sample_bouton_density', return_value=np.array([1., 3.]))
def test_1(_):
    expected = {
        ('*', '*'): {
            'bouton_reduction_factor': 5.0
        }
    }
    circuit = Mock()
    actual = test_module.execute('circuit', bio_data=10.0)
    nt.assert_equal(actual, expected)


@patch(test_module.__name__ + '.sample_bouton_density', return_value=np.array([1., 3.]))
def test_2(_):
    expected = {
        ('*', '*'): {
            'bouton_reduction_factor': 21.0
        }
    }
    actual = test_module.execute('circuit', bio_data=os.path.join(TEST_DATA_DIR, "bouton_density.tsv"))
    nt.assert_equal(actual, expected)
