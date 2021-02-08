import os
from itertools import chain

import numpy as np
from bluepy import Circuit
from mock import MagicMock, patch
from parameterized import param, parameterized
from pytest import approx

import connectome_tools.s2f_recipe.estimate_syns_con as test_module

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")


@parameterized.expand(
    [
        param(
            _="specific_formula",
            mtypes={"L6_TPC:C", "L4_CHC"},
            synapse_count=[1.0, 3.0, 4.0, 11.0, 7.0],
            kwargs={
                "formula": "1.3 * n",
                "formula_ee": "1.5 * n",
                "formula_ei": "1.6 * n",
                "formula_ie": "1.7 * n",
                "formula_ii": "1.8 * n",
                "max_value": 25.0,
                "sample": None,
            },
            expected={
                ("L4_CHC", "L4_CHC"): {"mean_syns_connection": approx(9.36)},
                ("L4_CHC", "L6_TPC:C"): {"mean_syns_connection": approx(8.84)},
                ("L6_TPC:C", "L4_CHC"): {"mean_syns_connection": approx(8.32)},
                ("L6_TPC:C", "L6_TPC:C"): {"mean_syns_connection": approx(7.80)},
            },
        ),
        param(
            _="generic_formula",
            mtypes={"L6_TPC:C", "L4_CHC"},
            synapse_count=[1.0, 3.0, 4.0, 11.0, 7.0],
            kwargs={"formula": "1.3 * n", "max_value": 25.0, "sample": None},
            expected={
                ("L4_CHC", "L4_CHC"): {"mean_syns_connection": approx(6.76)},
                ("L4_CHC", "L6_TPC:C"): {"mean_syns_connection": approx(6.76)},
                ("L6_TPC:C", "L4_CHC"): {"mean_syns_connection": approx(6.76)},
                ("L6_TPC:C", "L6_TPC:C"): {"mean_syns_connection": approx(6.76)},
            },
        ),
        param(
            _="formula_nan_as_1.0",
            mtypes={"L6_TPC:C", "L4_CHC"},
            synapse_count=[1.0, 2.0],
            kwargs={"formula": "6 * ((n - 2) ** 0.5) - 1", "max_value": 25.0, "sample": None},
            expected={
                ("L4_CHC", "L4_CHC"): {"mean_syns_connection": 1.0},
                ("L4_CHC", "L6_TPC:C"): {"mean_syns_connection": 1.0},
                ("L6_TPC:C", "L4_CHC"): {"mean_syns_connection": 1.0},
                ("L6_TPC:C", "L6_TPC:C"): {"mean_syns_connection": 1.0},
            },
        ),
        param(
            _="sample_file",
            mtypes={"SLM_PPA"},
            synapse_count=[1.0, 3.0, 4.0, 11.0, 7.0],
            kwargs={
                "formula": "1.3 * n",
                "max_value": 25.0,
                "sample": os.path.join(TEST_DATA_DIR, "nsyn_per_connection.tsv"),
            },
            expected={("SLM_PPA", "SLM_PPA"): {"mean_syns_connection": approx(21.06)}},
        ),
        param(
            _="sample_dict",
            mtypes={"SLM_PPA"},
            synapse_count=[1.0, 3.0, 4.0, 11.0, 7.0],
            kwargs={
                "formula": "1.3 * n",
                "max_value": 25.0,
                "sample": {"size": 10, "pre": 1, "post": 2},
            },
            expected={("SLM_PPA", "SLM_PPA"): {"mean_syns_connection": approx(6.76)}},
        ),
        param(
            _="no_synapse_count",
            mtypes={"SLM_PPA"},
            synapse_count=[],
            kwargs={"formula": "1.3 * n", "max_value": 25.0},
            expected={},
        ),
    ]
)
@patch(test_module.__name__ + ".sample_pathway_synapse_count")
def test_prepare(mock_synapse_count, _, mtypes, synapse_count, kwargs, expected):
    mock_synapse_count.return_value = np.array(synapse_count)
    circuit = MagicMock(Circuit)
    circuit.config = {}
    circuit.cells.mtypes = mtypes
    circuit.cells.get.return_value.drop_duplicates.return_value.values = np.array(
        [["L6_TPC:C", "EXC"], ["L4_CHC", "INH"], ["SLM_PPA", "EXC"], ["SP_AA", "INH"]]
    )

    task_generator = test_module.prepare(circuit, **kwargs)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected
