import os
import re

import pytest
from jsonschema import ValidationError
from mock import Mock, patch
from psutil import Process
from utils import TEST_DATA_DIR

import connectome_tools.utils as test_module

_this_process = Mock(
    Process,
    **{"as_dict.return_value": {"pid": 1, "name": "N1", "username": "U1", "cmdline": "CMD1"}},
)


@patch(test_module.__name__ + ".psutil.Process", return_value=_this_process)
def test_exit_if_not_alone_with_single_process(process):
    with patch(
        test_module.__name__ + ".psutil.process_iter",
        return_value=iter(
            [
                Mock(Process, info={"pid": 1, "name": "N1", "username": "U1", "cmdline": "CMD1"}),
                Mock(Process, info={"pid": 2, "name": "N1", "username": "U1", "cmdline": "CMD2"}),
            ]
        ),
    ):
        result = test_module.exit_if_not_alone()
        assert result is None


@patch(test_module.__name__ + ".psutil.Process", return_value=_this_process)
def test_exit_if_not_alone_with_multiple_processes(process):
    with patch(
        test_module.__name__ + ".psutil.process_iter",
        return_value=iter(
            [
                Mock(Process, info={"pid": 1, "name": "N1", "username": "U1", "cmdline": "CMD1"}),
                Mock(Process, info={"pid": 2, "name": "N1", "username": "U1", "cmdline": "CMD1"}),
            ]
        ),
    ):
        with pytest.raises(SystemExit) as exc_info:
            test_module.exit_if_not_alone()
        assert exc_info.value.args[0] == 1


def test_runalone():
    @test_module.runalone
    def f():
        return "DONE"

    with patch(test_module.__name__ + ".exit_if_not_alone") as mocked:
        result = f()
        assert result == "DONE"
        mocked.assert_called_once()


@pytest.mark.parametrize(
    "config_file, schema_name",
    [
        ("s2f_config_1.yaml", "strategies"),
        ("s2f_config_1_with_constraints.yaml", "strategies"),
        ("merge_config.yaml", "merge_config"),
        ("executor_config.yaml", "executor_config"),
    ],
)
def test_validate_config_success(config_file, schema_name):
    config = test_module.load_yaml(TEST_DATA_DIR / config_file)

    result = test_module.validate_config(config, schema_name)
    assert result is None


def test_validate_strategies_failure_1():
    config_file = "s2f_config_1.yaml"
    schema_name = "strategies"
    config = test_module.load_yaml(TEST_DATA_DIR / config_file)
    config.append({"unknown_strategy": {}})
    expected_error = "{'unknown_strategy': {}} is not valid under any of the given schemas"

    with pytest.raises(ValidationError, match=re.escape(expected_error)):
        test_module.validate_config(config, schema_name)


def test_validate_strategies_failure_2():
    config_file = "s2f_config_1.yaml"
    schema_name = "strategies"
    config = test_module.load_yaml(TEST_DATA_DIR / config_file)
    sample = config[2]["estimate_bouton_reduction"]["sample"]
    sample["wrong_attribute"] = sample.pop("assume_syns_bouton")
    expected_error = "Additional properties are not allowed ('wrong_attribute' was unexpected)"

    with pytest.raises(ValidationError, match=re.escape(expected_error)):
        test_module.validate_config(config, schema_name)


def test_validate_strategies_failure_3():
    config_file = "s2f_config_1.yaml"
    schema_name = "strategies"
    config = test_module.load_yaml(TEST_DATA_DIR / config_file)
    del config[2]["estimate_bouton_reduction"]["bio_data"]
    expected_error = "'bio_data' is a required property"

    with pytest.raises(ValidationError, match=re.escape(expected_error)):
        test_module.validate_config(config, schema_name)


def test_validate_strategies_failure_4():
    config_file = "s2f_config_1_with_constraints.yaml"
    schema_name = "strategies"
    config = test_module.load_yaml(TEST_DATA_DIR / config_file)
    add_constraints = config[6]["add_constraints"]
    add_constraints["from_region"] = add_constraints.pop("fromRegion")
    expected_error = "'from_region' does not match any of the regexes"

    with pytest.raises(ValidationError, match=re.escape(expected_error)):
        test_module.validate_config(config, schema_name)


def test_validate_strategies_failure_5():
    config_file = "s2f_config_1.yaml"
    schema_name = "strategies"
    config = test_module.load_yaml(TEST_DATA_DIR / config_file)
    override_mtype = config[5]["override_mtype"]
    # invalidate the configuration: remove p_A and add mean_syns_connection
    del override_mtype["p_A"]
    override_mtype["mean_syns_connection"] = 1.0
    expected_error = (
        "{'mtype_pattern': 'CHC', 'bouton_reduction_factor': 1.0, "
        "'pMu_A': 0.0, 'mean_syns_connection': 1.0} is not valid under any of the given schemas"
    )

    with pytest.raises(ValidationError, match=re.escape(expected_error)):
        test_module.validate_config(config, schema_name)


def test_clean_slurm_env():
    with patch.dict(
        os.environ,
        dict(
            SLURMD_NODENAME="r1i7n31",
            SLURM_JOB_PARTITION="interactive",
            SLURM_JOB_ACCOUNT="proj30",
            SLURM_NODEID="0",
            PMI_RANK="0",
        ),
        clear=True,
    ):
        test_module.clean_slurm_env()

        assert os.environ == dict(
            SLURMD_NODENAME="r1i7n31",
            SLURM_JOB_PARTITION="interactive",
            SLURM_JOB_ACCOUNT="proj30",
        )
