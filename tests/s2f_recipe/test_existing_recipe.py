import os
from itertools import chain

from bluepy.v2 import Circuit
from mock import MagicMock

import connectome_tools.s2f_recipe.existing_recipe as test_module

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")


def test_prepare():
    circuit = MagicMock(Circuit)
    recipe_path = os.path.join(TEST_DATA_DIR, "s2f_recipe_2.xml")
    expected = {
        ("L6_CHC", "L6_BTC"): {
            "bouton_reduction_factor": 1.0,
            "pMu_A": 0.0,
            "p_A": 1.0,
        },
        ("SLM_PPA", "SLM_PPA"): {
            "bouton_reduction_factor": 0.459,
            "cv_syns_connection": 0.348,
            "mean_syns_connection": 4.341,
        },
        ("SLM_PPA", "SP_AA"): {
            "bouton_reduction_factor": 0.184,
            "cv_syns_connection": 0.348,
            "mean_syns_connection": 3.47,
        },
    }

    worker_generator = test_module.prepare(circuit, recipe_path=recipe_path)
    result_generator = (worker() for worker in worker_generator)
    actual = dict(chain.from_iterable(result_generator))

    assert actual == expected
