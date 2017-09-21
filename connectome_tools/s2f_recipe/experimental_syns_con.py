"""
This strategy uses the biological mean number of
synapses per connection for a number of pathways where it
has been experimentally determined.
"""

from connectome_tools.dataset import read_nsyn
from connectome_tools.s2f_recipe import MEAN_SYNS_CONNECTION


def execute(circuit, bio_data):
    # pylint: disable=missing-docstring
    bio_data = read_nsyn(bio_data, mtypes=circuit.v2.cells.mtypes)
    return {
        (row['from'], row['to']): {
            MEAN_SYNS_CONNECTION: row['mean']
        }
        for _, row in bio_data.iterrows()  # pylint2: disable=maybe-no-member
    }
