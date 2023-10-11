import os
from itertools import chain

from bluepysnap.edges import EdgePopulation
from mock import MagicMock, patch
from utils import TEST_DATA_DIR

import connectome_tools.s2f_recipe.experimental_syns_con as test_module


@patch.object(test_module, "get_edge_population_mtypes")
def test_prepare(mock_get_mtypes):
    population = MagicMock(EdgePopulation)
    mock_get_mtypes.return_value = {"SLM_PPA", "SP_AA"}
    bio_data = os.path.join(TEST_DATA_DIR, "nsyn_per_connection.tsv")
    expected = {
        ("SLM_PPA", "SLM_PPA"): {"mean_syns_connection": 16.2},
        ("SLM_PPA", "SP_AA"): {"mean_syns_connection": 3.0},
    }

    task_generator = test_module.Executor().prepare(population, bio_data=bio_data)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected
