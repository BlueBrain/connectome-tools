"""
This strategy will estimate a reduction factor based for each
individual m-type. It takes into account the variability in the bouton
densities between m-types (e.g. pyramidal cells have lower density),
unless argument target_density is provided in which case that density
will be used for all m-types.
"""

import logging
import pandas as pd

from bluepy.v2.enums import Cell

from bluerecipe.bio_data import read_bouton_density
from bluerecipe.params import BOUTON_REDUCTION_FACTOR


L = logging.getLogger(__name__)


def execute(circuit, bio_data, sample_size=100, sample_target=None, assume_syns_bouton=1.0):
    # pylint: disable=missing-docstring
    mtypes = circuit.v2.cells.mtypes
    if isinstance(bio_data, float):
        ref_data = pd.DataFrame({
            'mtype': mtypes,
            'mean': bio_data,
        })
    else:
        ref_data = read_bouton_density(bio_data, mtypes=mtypes, logger=L)

    result = {}
    for _, row in ref_data.iterrows():
        mtype, ref_value = row['mtype'], row['mean']
        group = {Cell.MTYPE: mtype}
        if sample_target is not None:
            group['$target'] = sample_target
        sample = circuit.v2.stats.sample_bouton_density(
            n=sample_size, group=group, synapses_per_bouton=assume_syns_bouton
        )
        if len(sample) > 0:
            estimate = sample.mean()
            L.debug("Bouton density estimate for '%s': %.3f", mtype, estimate)
        else:
            L.warning("No '%s' cell in sample target", mtype)
            continue
        result[(mtype, '*')] = {
            BOUTON_REDUCTION_FACTOR: ref_value / estimate
        }

    return result
