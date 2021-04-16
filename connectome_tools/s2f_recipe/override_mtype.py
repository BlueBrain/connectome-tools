"""Strategy override_mtype.

This strategy is to be used last and overrides parameters for a subset of mtypes.
This is meant to avoid excessive pruning that would otherwise
happen due to the special nature of ChC synapses on the axon.
(more precisely: one touch actually represents a train of 5 synapses
and therefore the syns per con calculation would be off by that factor).
"""

from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.utils import Task


class Executor(BaseExecutor):
    """Executor class for override_mtype strategy."""

    is_parallel = False

    def prepare(self, circuit, mtype_pattern, **kwargs):
        """Yield tasks that should be executed.

        Args:
            circuit (bluepy.Circuit): circuit instance.
            mtype_pattern (str): substring of mtype used for matching.
            kwargs (dict): arguments to be set when mtype_pattern is a substring of mtype.

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ
        yield Task(_execute, circuit.cells.mtypes, mtype_pattern, task_group=__name__, **kwargs)


def _execute(mtypes, mtype_pattern, **kwargs):
    return [((mtype, "*"), kwargs) for mtype in mtypes if mtype_pattern in mtype]
