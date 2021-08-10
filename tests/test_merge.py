import logging
import shutil
from pathlib import Path

from mock import Mock, patch
from utils import TEST_DATA_DIR, canonicalize_xml, tmp_cwd, xml_to_regular_dict

import connectome_tools.merge as test_module
from connectome_tools.merge import RECIPES_DIR, SLURM_DIR, WORKDIR
from connectome_tools.utils import load_yaml
from connectome_tools.version import __version__


def test_execute_pending_tasks_success():
    pending_tasks = [Mock(), Mock(), Mock()]
    executor_params = {"timeout_min": 1}
    with tmp_cwd() as tmp_dir:
        folder = Path(tmp_dir)
        # Execute tasks in the same process using cluster='debug' because mocks cannot be pickled.
        # Do not test failures, because DebugJob.results() would start pdb and wait for stdin.
        failures = test_module.execute_pending_tasks(
            pending_tasks, executor_params, folder, cluster="debug"
        )

    assert failures == 0
    assert all(task.run.call_count == 1 for task in pending_tasks)


def test_delete_temporary_dirs():
    with tmp_cwd() as tmp_dir:
        workdir = Path(tmp_dir) / WORKDIR
        slurm_dir = workdir / SLURM_DIR
        recipes_dir = workdir / RECIPES_DIR
        slurm_dir.mkdir(parents=True)
        (slurm_dir / "some_file").touch()  # this dir isn't empty
        assert slurm_dir.exists() is True  # and it will be deleted
        assert recipes_dir.exists() is False  # this dir doesn't exist and it will be ignored

        test_module.delete_temporary_dirs(workdir)

        assert slurm_dir.exists() is False
        assert recipes_dir.exists() is False


@patch(test_module.__name__ + ".s2f_recipe.main")
def test_create_partial_recipe_run(s2f_recipe_main_mock):
    task = test_module.CreatePartialRecipe(
        strategies=[],
        base_path=Path(),
        circuit=Path(),
        seed=0,
        jobs=1,
        log_level=logging.INFO,
    )
    task.run()

    assert s2f_recipe_main_mock.call_count == 1


def test_create_partial_recipe_properties():
    task = test_module.CreatePartialRecipe(
        strategies=[{"add_constraints": {"toRegion": "PP2/3", "fromRegion": "SS2/3"}}],
        base_path=Path("/fake/absolute/path/to/recipes"),
        circuit=Path("/fake/absolute/path/to/circuitConfig"),
        seed=0,
        jobs=1,
        log_level=logging.INFO,
    )

    assert task.name == "fromRegion:SS2/3,toRegion:PP2/3"
    assert task.checksum == "4eece99e4a033783bb92a2000a161c4e"
    assert task.output == Path(
        "/fake/absolute/path/to/recipes/"
        "recipe_fromRegion%3ASS2%2F3%2CtoRegion%3APP2%2F3_4eece99e4a033783bb92a2000a161c4e.xml"
    )


def test_create_partial_recipe_properties_without_constraints():
    task = test_module.CreatePartialRecipe(
        strategies=[],
        base_path=Path("/fake/absolute/path/to/recipes"),
        circuit=Path("/fake/absolute/path/to/circuitConfig"),
        seed=0,
        jobs=1,
        log_level=logging.INFO,
    )

    assert task.name == "MISSING_CONSTRAINTS"
    assert task.checksum == "6b719f4c5395c21418fae503d862585b"
    assert task.output == Path(
        "/fake/absolute/path/to/recipes/"
        "recipe_MISSING_CONSTRAINTS_6b719f4c5395c21418fae503d862585b.xml"
    )


@patch(test_module.__name__ + ".execute_pending_tasks")
def test_create_full_recipe_run(execute_pending_tasks_mock):
    merge_config_path = TEST_DATA_DIR / "merge_config.yaml"
    executor_config_path = TEST_DATA_DIR / "executor_config.yaml"
    expected_recipe = TEST_DATA_DIR / "s2f_recipe_merged.xml"
    with tmp_cwd() as tmp_dir:
        tmp_path = Path(tmp_dir)
        workdir = tmp_path / WORKDIR
        recipe_path = tmp_path / "builderConnectivityRecipeAllPathways.xml"
        circuit = tmp_path / "CircuitConfig"
        circuit.touch()  # CircuitConfig must exist

        def _execute_pending_tasks(pending_tasks, *args, **kwargs):
            for n, task in enumerate(pending_tasks, 1):
                shutil.copy(TEST_DATA_DIR / f"s2f_recipe_partial_{n}.xml", task.output)
            return 0

        # replace execute_pending_tasks to simulate the execution of the tasks
        execute_pending_tasks_mock.side_effect = _execute_pending_tasks

        task = test_module.CreateFullRecipe(
            main_config=load_yaml(merge_config_path),
            executor_config=load_yaml(executor_config_path),
            circuit=circuit,
            workdir=workdir,
            output=recipe_path,
            seed=0,
            jobs=1,
            log_level=logging.INFO,
        )
        task.run()

        assert recipe_path.exists()

        # compare the xml converted to dicts (easier to find differences)
        actual_dict = xml_to_regular_dict(recipe_path)
        expected_dict = xml_to_regular_dict(expected_recipe)
        assert actual_dict == expected_dict

        # compare the xml after canonicalization (including comments)
        actual_str = canonicalize_xml(recipe_path)
        expected_str = canonicalize_xml(expected_recipe)
        expected_str = expected_str.format(version=__version__, circuit=circuit)
        assert actual_str == expected_str
