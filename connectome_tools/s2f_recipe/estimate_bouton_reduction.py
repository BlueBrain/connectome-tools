"""Strategy estimate_bouton_reduction.

This strategy will estimate an overall reduction factor based
on an estimated mean bouton density over all m-types.
It does not take into account potential variability in the bouton densities
between m-types (e.g. pyramidal cells have lower density)
"""

import logging

import numpy as np

from connectome_tools.dataset import read_bouton_density
from connectome_tools.s2f_recipe import BOUTON_REDUCTION_FACTOR
from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.stats import sample_bouton_density
from connectome_tools.utils import Task

L = logging.getLogger(__name__)


class Executor(BaseExecutor):
    """Executor class for estimate_bouton_reduction strategy."""

    # is_parallel is False because `_execute` needs to be executed in the main process,
    # while the function `sample_bouton_density` will make use of subprocesses
    is_parallel = False

    def prepare(self, edge_population, bio_data, sample=None):
        """Yield tasks that should be executed.

        Args:
            edge_population (bluepysnap.EdgePopulation): edge population instance.
            bio_data: reference value (float)
                or name of the .tsv file containing bouton density data (str).
            sample: sample configuration (dict)
                or name of the .tsv file containing bouton density data (str).

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ
        yield Task(
            _execute,
            edge_population,
            bio_data,
            sample,
            n_jobs=self.jobs,
            task_group=__name__,
        )


def _execute(edge_population, bio_data, sample, n_jobs):
    if isinstance(bio_data, float):
        ref_value = bio_data
    else:
        bio_data = read_bouton_density(bio_data).set_index("mtype")
        ref_value = bio_data.loc["*"]["mean"]

    if isinstance(sample, str):
        dset = read_bouton_density(sample).set_index("mtype")
        value = dset.loc["*"]["mean"]
    else:
        if sample is None:
            sample = {}
        values = sample_bouton_density(
            population=edge_population,
            n=sample.get("size", 100),
            group=sample.get("target", None),
            mask=sample.get("mask", None),
            synapses_per_bouton=sample.get("assume_syns_bouton", 1.0),
            n_jobs=n_jobs,
        )
        value = np.nanmean(values)

    L.info("Bouton density estimate: %.3g", value)
    return [(("*", "*"), {BOUTON_REDUCTION_FACTOR: ref_value / value})]
