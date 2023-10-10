from itertools import chain

from bluepysnap.edges import EdgePopulation
from mock import MagicMock, patch
from parameterized import param, parameterized

import connectome_tools.s2f_recipe.override_mtype as test_module


@parameterized.expand(
    [
        param(
            _="params_1",
            kwargs={
                "mtype_pattern": "CHC",
                "bouton_reduction_factor": 1.0,
                "mean_syns_connection": 1.0,
                "cv_syns_connection": 1.0,
            },
            expected={
                ("L4_CHC", "*"): {
                    "bouton_reduction_factor": 1.0,
                    "mean_syns_connection": 1.0,
                    "cv_syns_connection": 1.0,
                },
            },
        ),
        param(
            _="params_2",
            kwargs={
                "mtype_pattern": "CHC",
                "bouton_reduction_factor": 1.0,
                "p_A": 1.0,
                "pMu_A": 0.0,
            },
            expected={
                ("L4_CHC", "*"): {
                    "bouton_reduction_factor": 1.0,
                    "p_A": 1.0,
                    "pMu_A": 0.0,
                },
            },
        ),
        param(
            _="invalid_mtype",
            kwargs={
                "mtype_pattern": "INVALID",
                "bouton_reduction_factor": 1.0,
                "p_A": 1.0,
                "pMu_A": 0.0,
            },
            expected={},
        ),
    ]
)
@patch.object(test_module, "get_mtypes_from_edge_population")
def test_prepare(mock_get_mtypes, _, kwargs, expected):
    population = MagicMock(EdgePopulation)
    mock_get_mtypes.return_value = {"L6_TPC:C", "L4_CHC"}

    task_generator = test_module.Executor().prepare(population, **kwargs)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected
