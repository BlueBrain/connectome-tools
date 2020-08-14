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
from bluepy.v2 import Cell, Circuit

from connectome_tools.dataset import read_bouton_density
from connectome_tools.s2f_recipe import BOUTON_REDUCTION_FACTOR
from connectome_tools.s2f_recipe.utils import Task
from connectome_tools.stats import sample_bouton_density

L = logging.getLogger(__name__)


def estimate_bouton_density(
    circuit_config, mtype, sample_size, sample_target, mask, assume_syns_bouton
):
    """ Mean bouton density for given mtype. """
    group = {Cell.MTYPE: mtype}
    if sample_target is not None:
        group["$target"] = sample_target
    circuit = Circuit(circuit_config)
    values = sample_bouton_density(
        circuit, n=sample_size, group=group, mask=mask, synapses_per_bouton=assume_syns_bouton
    )
    return np.nanmean(values)


def prepare(circuit, bio_data, sample=None):
    # pylint: disable=missing-docstring
    mtypes = circuit.cells.mtypes
    if isinstance(bio_data, float):
        bio_data = pd.DataFrame(
            {
                "mtype": mtypes,
                "mean": bio_data,
            }
        )
    else:
        bio_data = read_bouton_density(bio_data, mtypes=mtypes)

    if isinstance(sample, str):
        dset = read_bouton_density(sample).set_index("mtype")
        estimate = lambda mtype: dset.loc[mtype]["mean"]
    else:
        if sample is None:
            sample = {}
        estimate = partial(
            estimate_bouton_density,
            circuit_config=circuit.config,
            sample_size=sample.get("size", 100),
            sample_target=sample.get("target", None),
            mask=sample.get("mask", None),
            assume_syns_bouton=sample.get("assume_syns_bouton", 1.0),
        )

    for _, row in bio_data.iterrows():
        yield Task(_execute, row, estimate, task_group=__name__)


def _execute(row, estimate):
    mtype, ref_value = row["mtype"], row["mean"]
    value = estimate(mtype=mtype)
    if np.isnan(value):
        L.warning("Could not estimate '%s' bouton density, skipping", mtype)
        return []
    L.debug("Bouton density estimate for '%s': %.3g", mtype, value)
    return [((mtype, "*"), {BOUTON_REDUCTION_FACTOR: ref_value / value})]
