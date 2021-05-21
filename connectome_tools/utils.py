"""Common utilities."""
import logging
import sys
import time
from collections import namedtuple
from contextlib import contextmanager
from functools import partial, wraps

import numpy as np
import psutil
from bluepy import Cell
from joblib import Parallel, delayed

L = logging.getLogger(__name__)

_help_link = (
    "https://bbpteam.epfl.ch/documentation/projects"
    "/connectome-tools/latest/index.html#troubleshooting"
)


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
    try:
        yield
    finally:
        elapsed = time.monotonic() - start_time
        logger.info("%s: %.2f seconds", message, elapsed)


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


def cell_group(mtype, target=None):
    """Return a group that can be used to select cell ids with BluePy.

    Args:
        mtype (str): mtype.
        target (str): target/node_set.

    Returns:
        dict: cell group.
    """
    result = {Cell.MTYPE: mtype}
    if target is not None:
        result["$target"] = target
    return result
