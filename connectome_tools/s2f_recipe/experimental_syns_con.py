"""Strategy experimental_syns_con.

This strategy uses the biological mean number of
synapses per connection for a number of pathways where it
has been experimentally determined.
"""

from connectome_tools.dataset import read_nsyn
from connectome_tools.s2f_recipe import MEAN_SYNS_CONNECTION
from connectome_tools.s2f_recipe.utils import Task


def prepare(circuit, bio_data):
    # noqa: D103 # pylint: disable=missing-docstring
    yield Task(_execute, bio_data, mtypes=circuit.cells.mtypes, task_group=__name__)


def _execute(bio_data, mtypes):
    bio_data = read_nsyn(bio_data, mtypes=mtypes)
    return [
        ((row["from"], row["to"]), {MEAN_SYNS_CONNECTION: row["mean"]})
        for _, row in bio_data.iterrows()
    ]
