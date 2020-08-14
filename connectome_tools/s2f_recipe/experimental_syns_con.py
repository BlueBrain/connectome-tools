"""
This strategy uses the biological mean number of
synapses per connection for a number of pathways where it
has been experimentally determined.
"""
from functools import partial

from connectome_tools.dataset import read_nsyn
from connectome_tools.s2f_recipe import MEAN_SYNS_CONNECTION


def prepare(circuit, bio_data):
    # pylint: disable=missing-docstring
    yield partial(_worker, bio_data, mtypes=circuit.cells.mtypes)


def _worker(bio_data, mtypes):
    # pylint: disable=missing-docstring
    bio_data = read_nsyn(bio_data, mtypes=mtypes)
    return [
        ((row["from"], row["to"]), {MEAN_SYNS_CONNECTION: row["mean"]})
        for _, row in bio_data.iterrows()
    ]
