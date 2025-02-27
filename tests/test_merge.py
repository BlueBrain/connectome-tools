import logging
import shutil
from pathlib import Path

from mock import Mock, patch
from utils import TEST_DATA_DIR, canonicalize_xml, tmp_cwd, xml_to_regular_dict

import connectome_tools.merge as test_module
from connectome_tools import __version__
from connectome_tools.merge import RECIPES_DIR, SLURM_DIR, WORKDIR
from connectome_tools.utils import load_yaml


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
        edge_population="Foo",
        atlas_path="Foo",
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
        edge_population="Foo",
        atlas_path="Foo",
        seed=0,
        jobs=1,
        log_level=logging.INFO,
    )

    assert task.name == "fromRegion:SS2/3,toRegion:PP2/3"
    assert task.checksum == "58ba4557b59d20799dad060fa799255f"
    assert task.output == Path(
        "/fake/absolute/path/to/recipes/"
        "recipe_fromRegion%3ASS2%2F3%2CtoRegion%3APP2%2F3_58ba4557b59d20799dad060fa799255f.xml"
    )


def test_create_partial_recipe_properties_without_constraints():
    task = test_module.CreatePartialRecipe(
        strategies=[],
        base_path=Path("/fake/absolute/path/to/recipes"),
        circuit=Path("/fake/absolute/path/to/circuitConfig"),
        edge_population="Foo",
        atlas_path="Foo",
        seed=0,
        jobs=1,
        log_level=logging.INFO,
    )

    assert task.name == "MISSING_CONSTRAINTS"
    assert task.checksum == "bfbb7f0106ddc068cfd7b233a5031566"
    assert task.output == Path(
        "/fake/absolute/path/to/recipes/"
        "recipe_MISSING_CONSTRAINTS_bfbb7f0106ddc068cfd7b233a5031566.xml"
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
        circuit = tmp_path / "circuit_config.json"
        circuit.touch()  # circuit config must exist

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
            edge_population="Foo",
            atlas_path="Foo",
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
