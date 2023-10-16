from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from utils import TEST_DATA_DIR, tmp_cwd

from connectome_tools.apps import s2f_recipe_merge as test_module
from connectome_tools.merge import WORKDIR


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(test_module.cli, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.startswith("Usage")


@patch.object(test_module.CreateFullRecipe, "run")
def test_run(run_mock):
    runner = CliRunner()
    merge_config_path = TEST_DATA_DIR / "merge_config.yaml"
    executor_config_path = TEST_DATA_DIR / "executor_config.yaml"
    with tmp_cwd() as tmp_dir:
        tmp_path = Path(tmp_dir)
        workdir = tmp_path / WORKDIR
        recipe_path = tmp_path / "builderConnectivityRecipeAllPathways.xml"
        circuit = tmp_path / "CircuitConfig"
        circuit.touch()  # CircuitConfig must exist
        result = runner.invoke(
            test_module.run,
            [
                "--edge-population",
                "Foo",
                "--config",
                str(merge_config_path),
                "--executor-config",
                str(executor_config_path),
                "--output",
                str(recipe_path),
                "--workdir",
                str(workdir),
                "--seed",
                "0",
                "--jobs",
                "1",
                "-vv",
                str(circuit),
            ],
            catch_exceptions=False,
        )

    assert result.exit_code == 0
    assert result.output == ""
    assert run_mock.call_count == 1


@patch(test_module.__name__ + ".delete_temporary_dirs")
def test_clean(delete_temporary_dirs_mock):
    runner = CliRunner()
    result = runner.invoke(test_module.clean, catch_exceptions=False)

    assert result.exit_code == 0
    assert result.output == ""
    assert delete_temporary_dirs_mock.call_count == 1
