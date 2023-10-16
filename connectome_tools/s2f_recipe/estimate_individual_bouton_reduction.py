"""Strategy estimate_individual_bouton_reduction.

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

from connectome_tools.dataset import read_bouton_density
from connectome_tools.s2f_recipe import BOUTON_REDUCTION_FACTOR
from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.stats import sample_bouton_density
from connectome_tools.utils import Task, cell_group, get_edge_population_mtypes

L = logging.getLogger(__name__)


class Executor(BaseExecutor):
    """Executor class for estimate_individual_bouton_reduction strategy."""

    # is_parallel is False because `_execute` needs to be executed in the main process,
    # while the function `sample_bouton_density` will make use of subprocesses
    is_parallel = False

    def prepare(self, edge_population, bio_data, atlas_path, sample=None):
        """Yield tasks that should be executed.

        Args:
            edge_population (bluepysnap.EdgePopulation): edge population instance.
            bio_data: reference value (float)
                or name of the .tsv file containing bouton density data (str).
            atlas_path (str): Path to the atlas directory
            sample: sample configuration (dict)
                or name of the .tsv file containing bouton density data (str).

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ
        mtypes = get_edge_population_mtypes(edge_population)
        if isinstance(bio_data, float):
            bio_data = pd.DataFrame({"mtype": mtypes, "mean": bio_data})
        else:
            bio_data = read_bouton_density(bio_data, mtypes=mtypes)

        if isinstance(sample, str):
            dset = read_bouton_density(sample).set_index("mtype")

            def estimate(mtype):
                return dset.loc[mtype]["mean"]

        else:
            if sample is None:
                sample = {}
            estimate = partial(
                _estimate_bouton_density,
                node_set=sample.get("node_set", None),
                edge_population=edge_population,
                atlas_path=atlas_path,
                n=sample.get("size", 100),
                mask=sample.get("mask", None),
                synapses_per_bouton=sample.get("assume_syns_bouton", 1.0),
                n_jobs=self.jobs,
            )
        for _, row in bio_data.iterrows():
            yield Task(_execute, row, estimate, task_group=__name__)


def _execute(row, estimate):
    """Return a list of one tuple (pathway, params) for a single mtype."""
    mtype, ref_value = row["mtype"], row["mean"]
    value = estimate(mtype=mtype)
    if np.isnan(value):
        L.warning("Could not estimate '%s' bouton density, skipping", mtype)
        return []
    L.info("Bouton density estimate for '%s': %.3g", mtype, value)
    return [((mtype, "*"), {BOUTON_REDUCTION_FACTOR: ref_value / value})]


def _estimate_bouton_density(mtype, node_set, **kwargs):
    """Return the mean bouton density for the given mtype."""
    group = cell_group(mtype, node_set=node_set)
    values = sample_bouton_density(group=group, **kwargs)
    return np.nanmean(values)
