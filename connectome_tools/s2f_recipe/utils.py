"""
Common functions.
"""
import time
from collections import namedtuple
from functools import partial

import numpy as np


TaskResult = namedtuple("TaskResult", ["id", "group", "value", "elapsed"])


class Task:
    """ Callable task class. """

    def __init__(self, func, *args, task_group=None, **kwargs):
        """ Initialize the task.

        Args:
            func: Function that will be called when calling the object.
            *args: Positional arguments for func.
            **kwargs: Named arguments for func.
            task_group: Task group, that can be reused for multiple tasks.
        """
        self._func = partial(func, *args, **kwargs)
        self.group = task_group

    def __call__(self, task_id=None, seed=None, setup_logging=None):
        """ Execute the task.

        Args:
            task_id: Task id, should be unique.
            seed: Seed to initialize the random number generator in the subprocess.
            setup_logging: If not None, it must be a callable to configure logging.

        Returns:
            The task result (it should be serializable to be returned from different processes).
        """
        start_time = time.monotonic()
        if setup_logging:
            setup_logging()
        if seed is not None:
            np.random.seed(seed)
        result = self._func()
        elapsed = time.monotonic() - start_time
        return TaskResult(id=task_id, group=self.group, value=result, elapsed=elapsed)
