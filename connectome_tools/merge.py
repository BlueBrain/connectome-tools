"""Tasks to calculate partial recipes and merge them in a single final recipe."""
import dataclasses
import hashlib
import json
import logging
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote_plus

import lxml.etree as ET
import submitit
import yaml

from connectome_tools.apps import s2f_recipe
from connectome_tools.utils import setup_logging
from connectome_tools.version import __version__

L = logging.getLogger(__name__)

WORKDIR = ".s2f_recipe"  # used as default, can be customized
SLURM_DIR = "slurm"  # relative to workdir, fixed
RECIPES_DIR = "recipes"  # relative to workdir, fixed


def _dump_attributes(obj):
    """Return a dump of the attributes of a dataclass."""
    return json.dumps(dataclasses.asdict(obj), indent=2, default=str)


def _build_xml_tree(paths, comment):
    """Concatenate the recipes and return the resulting xml tree.

    Args:
        paths (list): list of paths of the recipes to be merged.
        comment (str): global comment to be added to the generated xml.

    Returns:
        ET.ElementTree: the resulting xml tree.
    """
    root = ET.Element("ConnectionRules")
    root.addprevious(ET.Comment(comment))
    parser = ET.XMLParser(remove_blank_text=True)
    for path in paths:
        partial_tree = ET.parse(str(path), parser=parser)
        partial_root = partial_tree.getroot()
        root.extend(partial_root.getchildren())
    return ET.ElementTree(root)


def _write_xml_tree(path, tree):
    """Write the merged recipe.

    Args:
        path (Path): path to the xml file that will be written.
        tree (ET.ElementTree): ElementTree object to be written.
    """
    with path.open("wb") as f:
        tree.write(f, pretty_print=True, xml_declaration=True, encoding="utf-8")


def execute_pending_tasks(pending_tasks, executor_params, folder, cluster=None):
    """Submit the specified tasks to Slurm and wait for their completion.

    Args:
        pending_tasks (list): list of tasks to be executed.
        executor_params (dict): configuration parameters for the executor.
        folder (Path): folder where the executor logs will be saved.
        cluster (str): Forces AutoExecutor to use the given environment.
            Use "local" to run jobs locally, "debug" to run jobs in the same process.

    Returns:
        int: number of failed tasks.
    """
    executor = submitit.AutoExecutor(folder=folder, cluster=cluster)
    executor.update_parameters(**executor_params)
    L.info("Submitting jobs...")
    jobs = executor.map_array(lambda t: t.run(), pending_tasks)
    L.info("Waiting for %s jobs to complete...", len(jobs))
    failures = 0
    for n, job in enumerate(submitit.helpers.as_completed(jobs, poll_frequency=10), 1):
        try:
            # don't need the result, but check if the job is successful
            job.results()
            result = "DONE"
        except Exception as ex:  # pylint: disable=broad-except
            result = f"FAILED [reason: {ex}]"
            failures += 1
        (task,) = job.submission().args
        name = task.name
        L.info("Completed job %s/%s, id=%s, name=%r: %s", n, len(jobs), job.job_id, name, result)
    return failures


def delete_temporary_dirs(workdir):
    """Delete the directories used for partial recipes and slurm logs.

    Args:
        workdir (Path): working directory containing the temporary directories to be deleted.
    """
    paths = [workdir / SLURM_DIR, workdir / RECIPES_DIR]
    for p in paths:
        if p.exists():
            L.warning("Removing %s", p)
            shutil.rmtree(p)
        else:
            L.warning("Skipping %s because it doesn't exist", p)


@dataclass(frozen=True)
class CreatePartialRecipe:
    """Task that creates and saves a partial recipe."""

    strategies: List
    base_path: Path
    circuit: Path
    seed: int
    jobs: int
    log_level: int

    @cached_property
    def name(self):
        """Return the task name based on the selection attributes."""
        params = {}
        for entry in self.strategies:
            # entry must be a dict containing only one strategy
            assert len(entry) == 1, "Only one key can be specified for the strategy"
            strategy, kwargs = next(iter(entry.items()))
            if strategy == "add_constraints":
                params.update(kwargs)
        if not params:
            return "MISSING_CONSTRAINTS"
        return ",".join(f"{k}:{v}" for k, v in sorted(params.items()))

    @cached_property
    def checksum(self):
        """Return a checksum of the task."""
        # The parameters used to calculate the checksum:
        # - must not change after the initialization
        # - should allow to identify if the task is the same, so it's not re-executed
        params = (
            str(self.circuit.resolve()),
            self.strategies,
            self.seed,
        )
        return hashlib.md5(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()

    @cached_property
    def output(self):
        """Return the path to the partial recipe."""
        safe_name = quote_plus(self.name)
        return self.base_path / f"recipe_{safe_name}_{self.checksum}.xml"

    def run(self):
        """Run the task to create the partial recipe."""
        # setup logging in the new process
        setup_logging(level=self.log_level)
        L.info(
            "Running sub task %r\nwith output %s\nand parameters:\n%s",
            self.name,
            self.output,
            _dump_attributes(self),
        )
        s2f_recipe.main(
            circuit=str(self.circuit),
            strategies=self.strategies,
            output=self.output,
            seed=self.seed,
            jobs=self.jobs,
        )

    def complete(self):
        """Return True if the partial recipe has been already generated and saved."""
        return self.output.is_file()


@dataclass(frozen=True)
class CreateFullRecipe:
    """Task that creates and saves the full recipe."""

    main_config: Dict
    executor_config: Dict
    circuit: Path
    workdir: Path
    output: Path
    seed: int
    jobs: int
    log_level: int

    @property
    def _slurm_path(self):
        return self.workdir / SLURM_DIR

    @property
    def _recipes_path(self):
        return self.workdir / RECIPES_DIR

    def run(self):
        """Run the task to create the full recipe."""
        L.info("Running main task with parameters:\n%s", _dump_attributes(self))

        # create the directory that will contain the partial recipes, if needed
        L.info("Recipes folder: %s", self._recipes_path)
        self._recipes_path.mkdir(parents=True, exist_ok=True)

        all_tasks = [
            CreatePartialRecipe(
                strategies=params["strategies"],
                base_path=self._recipes_path,
                circuit=self.circuit,
                seed=self.seed,  # all the tasks will use the same seed
                jobs=self.jobs,
                log_level=self.log_level,
            )
            for i, params in enumerate(self.main_config["regions"])
        ]
        pending_tasks = [task for task in all_tasks if not task.complete()]
        L.info(
            "Recipes already calculated: %s/%s",
            len(all_tasks) - len(pending_tasks),
            len(all_tasks),
        )

        if pending_tasks:
            folder = self._slurm_path / f"{datetime.now():%Y%m%dT%H%M%S}"
            L.info("Slurm folder: %s", folder)
            failures = execute_pending_tasks(
                pending_tasks, self.executor_config["executor"], folder
            )
            if failures:
                L.error("Some jobs didn't complete successfully, exiting.")
                sys.exit(1)

        # concatenate the files in the same order and write the final result
        L.info(
            "Merging %s recipes:\n%s",
            len(all_tasks),
            "\n".join(f"{n}: {task.name} [{task.output}]" for n, task in enumerate(all_tasks, 1)),
        )
        tree = _build_xml_tree(
            paths=[task.output for task in all_tasks],
            comment=(
                f"\nGenerated by s2f-recipe-merge=={__version__}"
                f"\nfrom circuit {self.circuit}"
                f"\nusing strategies (seed={self.seed}):"
                f"\n{yaml.dump(self.main_config, sort_keys=False)}"
            ),
        )
        L.info("Writing %s", self.output)
        _write_xml_tree(self.output, tree)
