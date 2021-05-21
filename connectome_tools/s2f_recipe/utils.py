"""Common functions."""
import logging
from abc import ABC, abstractmethod

from connectome_tools.utils import run_parallel, run_sequential, timed

L = logging.getLogger(__name__)


class BaseExecutor(ABC):
    """Abstract class that can be subclassed for each strategy."""

    def __init__(self, jobs=None, base_seed=None):
        """Create a new executor.

        Args:
            jobs: number of concurrent jobs, only for parallel executions.
            base_seed: initial random seed, only for parallel executions.
        """
        self.jobs = jobs
        self.base_seed = base_seed

    @property
    @abstractmethod
    def is_parallel(self):
        """Return True if the tasks should be executed in parallel, False otherwise."""

    @abstractmethod
    def prepare(self, *args, **kwargs):
        """Yield tasks that should be executed."""

    def run(self, *args, **kwargs):
        """Run the executor."""
        with timed(L, f"Executed strategy {self.name}"):
            L.info("Preparing strategy '%s'...", self.name)
            tasks = self.prepare(*args, **kwargs)
            if self.is_parallel:
                L.info("Running strategy '%s' in parallel...", self.name)
                results = run_parallel(tasks, self.jobs, self.base_seed)
            else:
                L.info("Running strategy '%s' sequentially...", self.name)
                results = run_sequential(tasks)
            return results

    @property
    def name(self):
        """Executor name."""
        return self.__module__
