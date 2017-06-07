"""
This strategy will estimate an overall reduction factor based
on an estimated mean bouton density over all m-types.
It does not take into account potential variability in the bouton densities
between m-types (e.g. pyramidal cells have lower density)
"""

import logging

from bluerecipe.params import BOUTON_REDUCTION_FACTOR


L = logging.getLogger('s2f_recipe')


def execute(circuit, bio_data, sample_size=100, sample_target=None, assume_syns_bouton=1.0):
    # pylint: disable=missing-docstring
    assert isinstance(bio_data, float)
    sample = circuit.v2.stats.sample_bouton_density(
        n=sample_size, group=sample_target, synapses_per_bouton=assume_syns_bouton
    )
    estimate = sample.mean()
    L.debug("Bouton density estimate: %.3f", estimate)
    return {
        ('*', '*'): {
            BOUTON_REDUCTION_FACTOR: bio_data / estimate
        }
    }
