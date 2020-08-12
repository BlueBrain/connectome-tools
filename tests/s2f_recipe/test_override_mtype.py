from bluepy.v2 import Circuit
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
def test_execute(_, kwargs, expected):
    circuit = MagicMock(Circuit)
    circuit.cells.mtypes = {"L6_TPC:C", "L4_CHC"}

    actual = test_module.execute(circuit, **kwargs)

    assert actual == expected
