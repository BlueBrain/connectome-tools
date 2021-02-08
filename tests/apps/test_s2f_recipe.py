import os

import lxml.etree as ET
from bluepy import Circuit
from click.testing import CliRunner
from mock import MagicMock, mock_open, patch
from parameterized import param, parameterized

from connectome_tools.apps import s2f_recipe as test_module
from connectome_tools.s2f_recipe.utils import Task

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "../data")

SAME = "SAME"


def canonicalize_xml(xml_data=None, from_file=None):
    """Normalise the XML data in a way that allows byte-by-byte comparisons.

    Note: python 3.8 provides xml.etree.ElementTree.canonicalize.

    Args:
        xml_data (str): XML data string (alternative to from_file).
        from_file (str): file path (alternative to xml_data).

    Returns:
        str: the canonical form of the provided XML data.
    """
    etree = ET.fromstring(xml_data) if xml_data is not None else ET.parse(from_file)
    return ET.tostring(etree, method="c14n2", with_comments=False, strip_text=True)


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


@parameterized.expand([param(jobs=1), param(jobs=2)])
@patch(test_module.__name__ + ".open")
@patch(test_module.__name__ + ".Circuit")
@patch(test_module.__name__ + ".override_mtype.prepare")
@patch(test_module.__name__ + ".generalized_cv.prepare")
@patch(test_module.__name__ + ".experimental_syns_con.prepare")
@patch(test_module.__name__ + ".existing_recipe.prepare")
@patch(test_module.__name__ + ".estimate_syns_con.prepare")
@patch(test_module.__name__ + ".estimate_individual_bouton_reduction.prepare")
@patch(test_module.__name__ + ".estimate_bouton_reduction.prepare")
def test_app(
    estimate_bouton_reduction,
    estimate_individual_bouton_reduction,
    estimate_syns_con,
    existing_recipe,
    experimental_syns_con,
    generalized_cv,
    override_mtype,
    mock_circuit,
    mock_file,
    jobs,
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
    mtypes = {"L1_DAC", "SO_OLM", "L4_CHC"}

    # mock open, used to read the configuration, and to write the result
    s2f_config_path = os.path.join(TEST_DATA_DIR, "s2f_config_1.yaml")
    config_reader = open(s2f_config_path)
    output_writer = mock_open()()
    mock_file.side_effect = [config_reader, output_writer]

    # file containing the expected result
    output_path = os.path.join(TEST_DATA_DIR, "s2f_recipe_1.xml")

    mock_circuit.return_value = circuit = MagicMock(Circuit)
    circuit.cells.mtypes = mtypes

    runner = CliRunner()
    result = runner.invoke(
        test_module.app,
        [
            "-s",
            "s2f_config_placeholder.yaml",
            "-o",
            "s2f_recipe_placeholder.xml",
            "--seed",
            "0",
            "--jobs",
            jobs,
            "CircuitConfig",
        ],
        catch_exceptions=False,
    )

    output_writer.write.assert_called_once()

    # Inspect the actual args used
    actual_xml = output_writer.write.call_args.args[0]
    actual_xml = canonicalize_xml(actual_xml)
    expected_xml = canonicalize_xml(from_file=output_path)
    # Compare the canonicalized XML content
    assert actual_xml == expected_xml

    # note: stdout is not printed, but it can be accessed in result.output
    assert result.exit_code == 0
