"""
This strategy uses the biological mean number of
synapses per connection for a number of pathways where it
has been experimentally determined.
"""

import os
import pandas as pd

from bluerecipe.params import MEAN_SYNS_CONNECTION


def execute(circuit, bio_data):
    # pylint: disable=missing-docstring
    assert os.path.exists(bio_data)
    data = pd.read_csv(bio_data, sep=r'\s+')
    mtypes = circuit.v2.stats.mtypes
    return {
        (row['from'], row['to']): {
            MEAN_SYNS_CONNECTION: row['mean']
        }
        for _, row in data.iterrows()  # pylint: disable=maybe-no-member
        if (row['from'] in mtypes) and (row['to'] in mtypes)
    }
