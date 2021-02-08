from itertools import chain

from bluepy import Circuit
from mock import MagicMock
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
def test_prepare(_, kwargs, expected):
    circuit = MagicMock(Circuit)
    circuit.cells.mtypes = {"L6_TPC:C", "L4_CHC"}

    task_generator = test_module.prepare(circuit, **kwargs)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected
