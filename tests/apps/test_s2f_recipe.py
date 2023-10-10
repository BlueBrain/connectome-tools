from pathlib import Path

from bluepysnap.edges import EdgePopulation
from click.testing import CliRunner
from mock import MagicMock, patch
from parameterized import param, parameterized
from utils import TEST_DATA_DIR, tmp_cwd, xml_to_regular_dict

from connectome_tools.apps import s2f_recipe as test_module
from connectome_tools.utils import Task

SAME = "SAME"


def task_generator(data):
    def _execute(_items):
        return _items

    for items in data:
        yield Task(_execute, items)


def test_app_help():
    runner = CliRunner()
    result = runner.invoke(test_module.app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.startswith("Usage")


@parameterized.expand(
    [
        param(
            _="valid_1",
            pathways_dict={
                "bouton_reduction_factor": 1.0,
                "mean_syns_connection": 1.0,
                "cv_syns_connection": 1.0,
            },
            expected_is_valid=True,
            expected_missing=None,
            expected_dict=SAME,
        ),
        param(
            _="valid_2",
            pathways_dict={"bouton_reduction_factor": 1.0, "p_A": 1.0, "pMu_A": 0.0},
            expected_is_valid=True,
            expected_missing=None,
            expected_dict=SAME,
        ),
        param(
            _="valid_after_cleaning",
            pathways_dict={
                "bouton_reduction_factor": 1.0,
                "mean_syns_connection": 1.0,
                "cv_syns_connection": 1.0,
                "p_A": 1.0,
                "pMu_A": 0.0,
            },
            expected_is_valid=True,
            expected_missing=None,
            expected_dict={"bouton_reduction_factor": 1.0, "p_A": 1.0, "pMu_A": 0.0},
        ),
        param(
            _="missing_param_1",
            pathways_dict={
                "bouton_reduction_factor": 1.0,
                "mean_syns_connection": 1.0,
                "cv_syns_connection": 1.0,
                "p_A": 1.0,
            },
            expected_is_valid=False,
            expected_missing={"pMu_A"},
            expected_dict=SAME,
        ),
        param(
            _="missing_param_2",
            pathways_dict={},
            expected_is_valid=False,
            expected_missing={"bouton_reduction_factor"},
            expected_dict=SAME,
        ),
        param(
            _="missing_param_3",
            pathways_dict={"bouton_reduction_factor": 1.0},
            expected_is_valid=False,
            expected_missing={"mean_syns_connection", "cv_syns_connection"},
            expected_dict=SAME,
        ),
        param(
            _="missing_param_4",
            pathways_dict={"bouton_reduction_factor": 1.0, "mean_syns_connection": 1.0},
            expected_is_valid=False,
            expected_missing={"cv_syns_connection"},
            expected_dict=SAME,
        ),
    ]
)
def test_validate_params(_, pathways_dict, expected_is_valid, expected_missing, expected_dict):
    # if expected_dict is SAME, then we expect that pathways_dict will not be modified
    if expected_dict == SAME:
        expected_dict = pathways_dict.copy()

    is_valid, missing = test_module.validate_params(pathways_dict)

    assert is_valid == expected_is_valid
    assert missing == expected_missing
    assert pathways_dict == expected_dict


@parameterized.expand(
    [
        param(
            jobs=1,
            s2f_config_file="s2f_config_1.yaml",
            expected_recipe_file="s2f_recipe_1.xml",
        ),
        param(
            jobs=2,
            s2f_config_file="s2f_config_1.yaml",
            expected_recipe_file="s2f_recipe_1.xml",
        ),
        param(
            jobs=1,
            s2f_config_file="s2f_config_1_with_constraints.yaml",
            expected_recipe_file="s2f_recipe_1_with_constraints.xml",
        ),
    ]
)
@patch(test_module.__name__ + ".Circuit")
@patch.object(test_module.override_mtype.Executor, "prepare")
@patch.object(test_module.generalized_cv.Executor, "prepare")
@patch.object(test_module.experimental_syns_con.Executor, "prepare")
@patch.object(test_module.existing_recipe.Executor, "prepare")
@patch.object(test_module.estimate_syns_con.Executor, "prepare")
@patch.object(test_module.estimate_individual_bouton_reduction.Executor, "prepare")
@patch.object(test_module.estimate_bouton_reduction.Executor, "prepare")
@patch.object(test_module, "get_mtypes_from_edge_population")
def test_app(
    mock_get_mtypes,
    estimate_bouton_reduction,
    estimate_individual_bouton_reduction,
    estimate_syns_con,
    existing_recipe,
    experimental_syns_con,
    generalized_cv,
    override_mtype,
    mock_circuit,
    jobs,
    s2f_config_file,
    expected_recipe_file,
):
    # mock strategies
    estimate_bouton_reduction.return_value = task_generator(
        [[(("*", "*"), {"bouton_reduction_factor": 5.0})]]
    )
    estimate_individual_bouton_reduction.return_value = task_generator(
        [[(("SO_OLM", "*"), {"bouton_reduction_factor": 11.0})]]
    )
    estimate_syns_con.return_value = task_generator(
        [
            [(("L1_DAC", "L1_DAC"), {"mean_syns_connection": 6.0})],
            [(("L1_DAC", "SO_OLM"), {"mean_syns_connection": 7.0})],
            [(("L1_DAC", "L4_CHC"), {"mean_syns_connection": 8.0})],
            [(("SO_OLM", "L1_DAC"), {"mean_syns_connection": 6.5})],
            [(("SO_OLM", "SO_OLM"), {"mean_syns_connection": 4.5})],
            [(("SO_OLM", "L4_CHC"), {"mean_syns_connection": 3.5})],
            [(("L4_CHC", "L1_DAC"), {"mean_syns_connection": 3.0})],
            [(("L4_CHC", "SO_OLM"), {"mean_syns_connection": 4.0})],
            [(("L4_CHC", "L4_CHC"), {"mean_syns_connection": 5.0})],
        ]
    )
    existing_recipe.return_value = task_generator([[]])
    experimental_syns_con.return_value = task_generator(
        [
            [
                (("L1_DAC", "L1_DAC"), {"mean_syns_connection": 7.5}),
                (("SO_OLM", "L4_CHC"), {"mean_syns_connection": 2.0}),
            ]
        ]
    )
    generalized_cv.return_value = task_generator([[(("*", "*"), {"cv_syns_connection": 0.32})]])
    override_mtype.return_value = task_generator(
        [[(("L4_CHC", "*"), {"bouton_reduction_factor": 1.0, "p_A": 1.0, "pMu_A": 0.0})]]
    )
    mock_get_mtypes.return_value = {"L1_DAC", "SO_OLM", "L4_CHC"}

    # file containing the expected result
    output_path = Path(TEST_DATA_DIR, expected_recipe_file)
    expected = xml_to_regular_dict(output_path)

    population = MagicMock(EdgePopulation)
    mock_circuit.edges = {"Foo": population}

    with tmp_cwd() as tmp_dir:
        config_path = Path(TEST_DATA_DIR, s2f_config_file)
        recipe_path = Path(tmp_dir, "s2f_recipe_result.xml")
        runner = CliRunner()
        result = runner.invoke(
            test_module.app,
            [
                "-s",
                config_path,
                "-o",
                recipe_path,
                "--seed",
                "0",
                "--jobs",
                jobs,
                "--population",
                "Foo",
                "CircuitConfig",
            ],
            catch_exceptions=False,
        )
        actual = xml_to_regular_dict(recipe_path)

    # note: stdout is not printed, but it can be accessed in result.output
    assert result.exit_code == 0
    assert actual == expected
