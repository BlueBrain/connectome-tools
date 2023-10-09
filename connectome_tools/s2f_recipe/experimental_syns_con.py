"""Strategy experimental_syns_con.

This strategy uses the biological mean number of
synapses per connection for a number of pathways where it
has been experimentally determined.
"""

from connectome_tools.dataset import read_nsyn
from connectome_tools.s2f_recipe import MEAN_SYNS_CONNECTION
from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.utils import Task, get_mtypes_from_edge_population


class Executor(BaseExecutor):
    """Executor class for experimental_syns_con strategy."""

    is_parallel = False

    def prepare(self, edge_population, bio_data):
        """Yield tasks that should be executed.

        Args:
            edge_population (bluepysnap.EdgePopulation): edge population instance.
            bio_data (str): name of the .tsv file containing experimental nsyn data.

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ
        mtypes = get_mtypes_from_edge_population(edge_population)
        yield Task(_execute, bio_data, mtypes=mtypes, task_group=__name__)


def _execute(bio_data, mtypes):
    bio_data = read_nsyn(bio_data, mtypes=mtypes)
    return [
        ((row["from"], row["to"]), {MEAN_SYNS_CONNECTION: row["mean"]})
        for _, row in bio_data.iterrows()
    ]
