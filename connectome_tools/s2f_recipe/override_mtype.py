"""Strategy override_mtype.

This strategy is to be used last and overrides parameters for a subset of mtypes.
This is meant to avoid excessive pruning that would otherwise
happen due to the special nature of ChC synapses on the axon.
(more precisely: one touch actually represents a train of 5 synapses
and therefore the syns per con calculation would be off by that factor).
"""

from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.utils import Task, get_edge_population_mtypes


class Executor(BaseExecutor):
    """Executor class for override_mtype strategy."""

    is_parallel = False

    def prepare(self, edge_population, mtype_pattern, **kwargs):
        """Yield tasks that should be executed.

        Args:
            edge_population (bluepysnap.EdgePopulation): edge population instance.
            mtype_pattern (str): substring of mtype used for matching.
            kwargs (dict): arguments to be set when mtype_pattern is a substring of mtype.

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ
        mtypes = get_edge_population_mtypes(edge_population)
        yield Task(_execute, mtypes, mtype_pattern, task_group=__name__, **kwargs)


def _execute(mtypes, mtype_pattern, **kwargs):
    return [((mtype, "*"), kwargs) for mtype in mtypes if mtype_pattern in mtype]
