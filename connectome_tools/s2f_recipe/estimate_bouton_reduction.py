"""
This strategy will estimate an overall reduction factor based
on an estimated mean bouton density over all m-types.
It does not take into account potential variability in the bouton densities
between m-types (e.g. pyramidal cells have lower density)
"""

import logging

import numpy as np

from connectome_tools.dataset import read_bouton_density
from connectome_tools.s2f_recipe import BOUTON_REDUCTION_FACTOR


L = logging.getLogger(__name__)


def execute(circuit, bio_data, sample=None):
    # pylint: disable=missing-docstring
    if isinstance(bio_data, float):
        ref_value = bio_data
    else:
        bio_data = read_bouton_density(bio_data).set_index('mtype')
        ref_value = bio_data.loc['*']['mean']

    if isinstance(sample, str):
        dset = read_bouton_density(sample).set_index('mtype')
        value = dset.loc['*']['mean']
    else:
        if sample is None:
            sample = {}
        values = circuit.v2.stats.sample_bouton_density(
            n=sample.get('size', 100),
            group=sample.get('target', None),
            region=sample.get('region', None),
            synapses_per_bouton=sample.get('assume_syns_bouton', 1.0)
        )
        value = np.nanmean(values)

    L.debug("Bouton density estimate: %.3g", value)

    return {
        ('*', '*'): {
            BOUTON_REDUCTION_FACTOR: ref_value / value
        }
    }
