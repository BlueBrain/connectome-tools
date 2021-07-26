import os
from itertools import chain

from bluepy import Circuit
from mock import MagicMock
from utils import TEST_DATA_DIR

import connectome_tools.s2f_recipe.experimental_syns_con as test_module


def test_prepare():
    circuit = MagicMock(Circuit)
    circuit.cells.mtypes = {"SLM_PPA", "SP_AA"}
    bio_data = os.path.join(TEST_DATA_DIR, "nsyn_per_connection.tsv")
    expected = {
        ("SLM_PPA", "SLM_PPA"): {"mean_syns_connection": 16.2},
        ("SLM_PPA", "SP_AA"): {"mean_syns_connection": 3.0},
    }

    task_generator = test_module.Executor().prepare(circuit, bio_data=bio_data)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected
