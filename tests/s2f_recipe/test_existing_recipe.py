import os
from itertools import chain

import pytest
from bluepy import Circuit
from mock import MagicMock
from parameterized import param, parameterized

import connectome_tools.s2f_recipe.existing_recipe as test_module

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")


@parameterized.expand(
    [
        param(recipe_name="s2f_recipe_2.xml"),
        param(recipe_name="s2f_recipe_2_old_format.xml"),
    ]
)
def test_prepare(recipe_name):
    circuit = MagicMock(Circuit)
    recipe_path = os.path.join(TEST_DATA_DIR, recipe_name)
    expected = {
        ("L6_CHC", "L6_BTC"): {
            "bouton_reduction_factor": "1.0",
            "pMu_A": "0.0",
            "p_A": "1.0",
        },
        ("SLM_PPA", "SLM_PPA"): {
            "bouton_reduction_factor": "0.459",
            "cv_syns_connection": "0.348",
            "mean_syns_connection": "4.341",
        },
        ("SLM_PPA", "SP_AA"): {
            "bouton_reduction_factor": "0.184",
            "cv_syns_connection": "0.348",
            "mean_syns_connection": "3.470",
        },
    }

    task_generator = test_module.Executor().prepare(circuit, recipe_path=recipe_path)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected


def test_duplicate_pathways():
    recipe_name = "s2f_recipe_3_duplicate_pathways.xml"
    circuit = MagicMock(Circuit)
    recipe_path = os.path.join(TEST_DATA_DIR, recipe_name)

    task_generator = test_module.Executor().prepare(circuit, recipe_path=recipe_path)
    result_generator = (task() for task in task_generator)
    with pytest.raises(ValueError, match="Rules using the same pathway cannot be imported"):
        dict(chain.from_iterable(item.value for item in result_generator))


def test_mixed_formats():
    recipe_name = "s2f_recipe_4_mixed_formats.xml"
    circuit = MagicMock(Circuit)
    recipe_path = os.path.join(TEST_DATA_DIR, recipe_name)

    task_generator = test_module.Executor().prepare(circuit, recipe_path=recipe_path)
    result_generator = (task() for task in task_generator)
    with pytest.raises(
        ValueError, match="Rules in different formats in the same file cannot be imported"
    ):
        dict(chain.from_iterable(item.value for item in result_generator))


def test_selection_attributes():
    recipe_name = "s2f_recipe_5_with_region_constraint.xml"
    circuit = MagicMock(Circuit)
    recipe_path = os.path.join(TEST_DATA_DIR, recipe_name)
    expected = {
        ("SLM_PPA", "SLM_PPA"): {
            "bouton_reduction_factor": "0.459",
            "cv_syns_connection": "0.348",
            "mean_syns_connection": "4.341",
            "fromRegion": "SSp-ll@right",
        },
    }

    task_generator = test_module.Executor().prepare(circuit, recipe_path=recipe_path)
    result_generator = (task() for task in task_generator)
    actual = dict(chain.from_iterable(item.value for item in result_generator))

    assert actual == expected
