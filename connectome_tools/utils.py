"""Common utilities."""

import logging
import os
import sys
import time
from collections import namedtuple
from collections.abc import Iterable
from contextlib import contextmanager
from functools import partial, wraps
from pathlib import Path
from urllib.request import urlopen

import click
import importlib_resources
import jsonschema
import numpy as np
import psutil
import yaml
from bluepysnap.query import NODE_SET_KEY
from joblib import Parallel, delayed

L = logging.getLogger(__name__)

FILE_PATH = click.Path(dir_okay=False, resolve_path=True)
DIR_PATH = click.Path(dir_okay=True, resolve_path=True)
EXISTING_FILE_PATH = click.Path(exists=True, readable=True, dir_okay=False, resolve_path=True)
EXISTING_DIR_PATH = click.Path(exists=True, readable=True, dir_okay=True, resolve_path=True)

# resource paths relative to the package root
SCHEMA_PATH = Path("data/schemas")
DEFAULT_CONFIG_PATH = Path("data/default_config")

_help_link = (
    "https://bbpteam.epfl.ch/documentation/projects"
    "/connectome-tools/latest/index.html#troubleshooting"
)


class Properties:
    """Properties used throughout the code."""

    MTYPE = "mtype"
    SYNAPSE_CLASS = "synapse_class"

    PRE_SECTION_ID = "efferent_section_id"
    PRE_SEGMENT_ID = "efferent_segment_id"

    SECTION_ID = "section_id"
    SEGMENT_ID = "segment_id"

    SEGMENT_X1 = "x1"
    SEGMENT_Y1 = "y1"
    SEGMENT_Z1 = "z1"

    SEGMENT_X2 = "x2"
    SEGMENT_Y2 = "y2"
    SEGMENT_Z2 = "z2"


def exit_if_not_alone():
    """Exit the program if there are other instances running on the same host."""
    attrs = ["pid", "name", "username", "cmdline"]
    this = psutil.Process().as_dict(attrs=attrs)
    others = [
        p.info
        for p in psutil.process_iter(attrs=attrs)
        if p.info["pid"] != this["pid"]
        and all(p.info[k] == this[k] for k in ["name", "username", "cmdline"])
    ]
    if others:
        L.error(
            "Only one instance can be executed at the same time! Exiting process with pid %s.\n"
            "See %s for more details.",
            this["pid"],
            _help_link,
        )
        sys.exit(1)


def runalone(func):
    """Decorator that terminates the process if other instances of the same program are running."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        exit_if_not_alone()
        return func(*args, **kwargs)

    return wrapper


@contextmanager
def timed(logger, message):
    """Context manager to log the execution time using the specified logger."""
    start_time = time.monotonic()
    status = None
    try:
        yield
    except BaseException:
        status = "FAILED"
        raise
    else:
        status = "DONE"
    finally:
        elapsed = time.monotonic() - start_time
        logger.info("%s: %.2f seconds [%s]", message, elapsed, status)


def setup_logging(level):
    """Setup logging."""
    # This function is called in the main process and in the tasks executed in a subprocess.
    # It does not reconfigure logging if it has been already configured in the same process.
    logformat = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(format=logformat, level=level)


def run_parallel(tasks, jobs, base_seed):
    """Run tasks in parallel."""
    level = L.getEffectiveLevel()
    setup_task_logging = partial(setup_logging, level=level)
    # If verbose is more than 10, all iterations are printed to stderr.
    # Above 50, the output is sent to stdout.
    verbose = 0 if level >= logging.WARNING else 10
    parallel = Parallel(n_jobs=jobs, backend="loky", verbose=verbose)
    return parallel(
        [
            delayed(task)(
                task_id=i,
                seed=None if base_seed is None else base_seed + i,
                setup_task_logging=setup_task_logging,
            )
            for i, task in enumerate(tasks)
        ]
    )


def run_sequential(tasks):
    """Run tasks sequentially in the current process."""
    return [task(task_id=i, seed=None, setup_task_logging=None) for i, task in enumerate(tasks)]


class Task:
    """Callable task class."""

    def __init__(self, func, *args, task_group=None, **kwargs):
        """Initialize the task.

        Args:
            func: Function that will be called when calling the object.
            *args: Positional arguments for func.
            **kwargs: Named arguments for func.
            task_group (string): Optional name of the group to which the task belong.
        """
        self._func = partial(func, *args, **kwargs)
        self.group = task_group

    def __call__(self, task_id=None, seed=None, setup_task_logging=None):
        """Execute the task.

        Args:
            task_id: Task id, should be unique.
            seed: Seed to initialize the random number generator in the subprocess.
            setup_task_logging: If not None, it must be a callable to configure logging.

        Returns:
            The task result (it should be serializable to be returned from different processes).
        """
        with timed(L, f"Executed task {task_id} for {self.group}"):
            start_time = time.monotonic()
            if setup_task_logging:
                setup_task_logging()
            if seed is not None:
                np.random.seed(seed)
            result = self._func()
            elapsed = time.monotonic() - start_time
            return TaskResult(id=task_id, group=self.group, value=result, elapsed=elapsed)


TaskResult = namedtuple("TaskResult", ["id", "group", "value", "elapsed"])


def cell_group(mtype, node_set=None):
    """Return a group that can be used to select cell ids with SNAP.

    Args:
        mtype (str): mtype.
        node_set (str): node_set.

    Returns:
        dict: cell group.
    """
    result = {Properties.MTYPE: mtype}
    if node_set is not None:
        result[NODE_SET_KEY] = node_set
    return result


def load_yaml(filepath):
    """Load YAML file."""
    with open(filepath, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_yaml_url(url):
    """Load YAML url."""
    with urlopen(url) as f:
        return yaml.safe_load(f)


def validate_config(config, schema_name):
    """Validate a configuration using the given schema name.

    To be able to resolve any reference, the schema $id should be omitted
    or set to the relative path of the local filename.

    Args:
        config (object): configuration to be validated.
        schema_name (str): name of the schema file without .yaml extension.
    """
    ref = importlib_resources.files(__package__) / SCHEMA_PATH / f"{schema_name}.yaml"
    with importlib_resources.as_file(ref) as path:
        # Define a custom resolver to resolve any local reference, and
        # a custom handler to load any reference in yaml format instead of json.
        resolver = jsonschema.RefResolver(
            base_uri=f"file://{path.parent}/", referrer=None, handlers={"file": load_yaml_url}
        )
        # Raise a ValidationError if the validation is not successful.
        jsonschema.validate(instance=config, schema=load_yaml(path), resolver=resolver)


def clean_slurm_env():
    """Remove PMI/SLURM variables that can cause issues when launching other slurm jobs.

    These variable are unset because launching slurm jobs with submitit from a node
    allocated using salloc would fail with the error:
        srun: fatal: SLURM_MEM_PER_CPU, SLURM_MEM_PER_GPU, and SLURM_MEM_PER_NODE
        are mutually exclusive.
    """
    for key in os.environ:
        if key.startswith(("PMI_", "SLURM_")) and not key.endswith(("_ACCOUNT", "_PARTITION")):
            L.debug("Deleting env variable %s", key)
            del os.environ[key]


def get_node_population_mtypes(population):
    """Get all unique mtypes from node population instance."""
    prop = Properties.MTYPE
    mtypes = population.property_values(prop) if prop in population.property_names else set()
    return sorted(mtypes)


def get_edge_population_mtypes(population):
    """Get all unique mtypes from edge population instance."""
    pre_mtypes = get_node_population_mtypes(population.source)
    post_mtypes = get_node_population_mtypes(population.target)

    return sorted(set(pre_mtypes + post_mtypes))


def is_iterable(v):
    """Return True if `v` is any iterable (strings are considered scalar)."""
    return isinstance(v, Iterable) and not isinstance(v, str)


def ensure_list(v):
    """Convert iterable / wrap scalar into list (strings are considered scalar)."""
    if is_iterable(v):
        return list(v)
    else:
        return [v]
