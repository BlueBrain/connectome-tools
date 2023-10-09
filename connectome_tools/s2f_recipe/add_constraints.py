"""Strategy add_constraints.

This strategy adds generic constraints to each rule.
"""

from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.utils import Task


class Executor(BaseExecutor):
    """Executor class for add_constraints strategy."""

    is_parallel = False

    def prepare(self, _, __, **constraints):
        """Yield tasks that should be executed.

        Args:
            constraints: constraints that will be added to all the rules.

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ
        yield Task(_execute, constraints, task_group=__name__)


def _execute(constraints):
    return [(("*", "*"), constraints)]
