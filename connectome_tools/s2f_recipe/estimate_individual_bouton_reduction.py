"""
This strategy will estimate a reduction factor based for each
individual m-type. It takes into account the variability in the bouton
densities between m-types (e.g. pyramidal cells have lower density),
unless argument target_density is provided in which case that density
will be used for all m-types.
"""

import logging

from functools import partial

import numpy as np
import pandas as pd

from bluepy.v2 import Cell

from connectome_tools.dataset import read_bouton_density
from connectome_tools.s2f_recipe import BOUTON_REDUCTION_FACTOR
from connectome_tools.stats import sample_bouton_density


L = logging.getLogger(__name__)


def estimate_bouton_density(circuit, mtype, sample_size, sample_target, region, assume_syns_bouton):
    """ Mean bouton density for given mtype. """
    group = {Cell.MTYPE: mtype}
    if sample_target is not None:
        group['$target'] = sample_target
    values = sample_bouton_density(
        circuit,
        n=sample_size, group=group, region=region, synapses_per_bouton=assume_syns_bouton
    )
    return np.nanmean(values)


def execute(circuit, bio_data, sample=None):
    # pylint: disable=missing-docstring
    mtypes = circuit.cells.mtypes
    if isinstance(bio_data, float):
        bio_data = pd.DataFrame({
            'mtype': mtypes,
            'mean': bio_data,
        })
    else:
        bio_data = read_bouton_density(bio_data, mtypes=mtypes)

    if isinstance(sample, str):
        dset = read_bouton_density(sample).set_index('mtype')
        estimate = lambda mtype: dset.loc[mtype]['mean']
    else:
        if sample is None:
            sample = {}
        estimate = partial(
            estimate_bouton_density,
            circuit=circuit,
            sample_size=sample.get('size', 100),
            sample_target=sample.get('target', None),
            region=sample.get('region', None),
            assume_syns_bouton=sample.get('assume_syns_bouton', 1.0)
        )

    result = {}
    for _, row in bio_data.iterrows():
        mtype, ref_value = row['mtype'], row['mean']
        value = estimate(mtype=mtype)
        if np.isnan(value):
            L.warn("Could not estimate '%s' bouton density, skipping", mtype)
            continue
        L.debug("Bouton density estimate for '%s': %.3g", mtype, value)
        result[(mtype, '*')] = {
            BOUTON_REDUCTION_FACTOR: ref_value / value
        }

    return result
