"""Strategy generalized_cv.

This strategy uses a generalized value of the coefficient
of variation of the number of synapses per connection.
"""

from connectome_tools.s2f_recipe import CV_SYNS_CONNECTION
from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.utils import Task


class Executor(BaseExecutor):
    """Executor class for generalized_cv strategy."""

    is_parallel = False

    def prepare(self, _, cv):
        """Yield tasks that should be executed.

        Args:
            cv (float): value to be used for cv_syns_connection.

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ
        yield Task(_execute, cv, task_group=__name__)


def _execute(cv):
    return [(("*", "*"), {CV_SYNS_CONNECTION: cv})]
