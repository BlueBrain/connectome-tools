"""
This strategy will estimate an overall reduction factor based
on an estimated mean bouton density over all m-types.
It does not take into account potential variability in the bouton densities
between m-types (e.g. pyramidal cells have lower density)
"""

import logging

from bluerecipe.bio_data import read_bouton_density
from bluerecipe.params import BOUTON_REDUCTION_FACTOR


L = logging.getLogger(__name__)


def execute(circuit, bio_data, sample_size=100, sample_target=None, assume_syns_bouton=1.0):
    # pylint: disable=missing-docstring
    if isinstance(bio_data, float):
        ref_value = bio_data
    else:
        ref_data = read_bouton_density(bio_data, mtypes=circuit.v2.cells.mtypes, logger=L)
        ref_value = ref_data['mean'].mean()

    sample = circuit.v2.stats.sample_bouton_density(
        n=sample_size, group=sample_target, synapses_per_bouton=assume_syns_bouton
    )
    estimate = sample.mean()
    L.debug("Bouton density estimate: %.3f", estimate)

    return {
        ('*', '*'): {
            BOUTON_REDUCTION_FACTOR: ref_value / estimate
        }
    }
