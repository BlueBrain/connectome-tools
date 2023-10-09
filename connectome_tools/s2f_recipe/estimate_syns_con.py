"""Strategy estimate_syns_con.

This strategy estimates the functional mean number of synapses per
connection from the structural number of appositions per connection.
For the prediction, an algebraic expression using 'n' (mean number of
appositions) can be specified as a string (see below).
"""

import itertools
import logging
from functools import partial

import numpy as np
import pandas as pd
from bluepysnap import Circuit
from bluepysnap.bbp import Cell
from Equation import Expression

from connectome_tools.dataset import read_nsyn
from connectome_tools.s2f_recipe import MEAN_SYNS_CONNECTION
from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.stats import sample_pathway_synapse_count
from connectome_tools.utils import Task, cell_group, get_mtypes_from_edge_population

L = logging.getLogger(__name__)


def _choose_formula(formulae, pathway, syn_class_map):
    """Choose formula based on pre- and post- synapse class (EXC | INH)."""
    custom = (syn_class_map[pathway[0]], syn_class_map[pathway[1]])
    if custom in formulae:
        return formulae[custom]
    else:
        return formulae[("*", "*")]


# TODO: should be able to pass circuit as an object (pickleable)
def _estimate_nsyn(circuit_config, population, pathway, sample_size, pre, post):
    """Mean nsyn for given mtype."""
    pre_mtype, post_mtype = pathway
    circuit = Circuit(circuit_config)
    values = sample_pathway_synapse_count(
        circuit,
        population,
        n=sample_size,
        pre=cell_group(pre_mtype, target=pre),
        post=cell_group(post_mtype, target=post),
    )
    # avoid RuntimeWarning: Mean of empty slice.
    return values.mean() if values.size else np.nan


class Executor(BaseExecutor):
    """Executor class for estimate_syns_con strategy."""

    is_parallel = True

    def prepare(
        self,
        circuit,
        edge_population,
        formula,
        formula_ee=None,
        formula_ei=None,
        formula_ie=None,
        formula_ii=None,
        max_value=None,
        sample=None,
    ):
        """Yield tasks that should be executed.

        Args:
            circuit (bluepysnap.Circuit): circuit instance.
            formula (str): default formula.
            formula_ee (str): formula for EXC-EXC pathways, it can be None to use the default.
            formula_ei (str): formula for EXC-INH pathways, it can be None to use the default.
            formula_ie (str): formula for INH-EXC pathways, it can be None to use the default.
            formula_ii (str): formula for INH-INH pathways, it can be None to use the default.
            max_value (float): maximum value used to cap the result, or None for no capping.
            sample: sample configuration (dict)
                or name of the .tsv file containing nsyn data (string).

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ, too-many-arguments
        formulae = {}
        formulae[("*", "*")] = Expression(formula)
        if formula_ee is not None:
            formulae[("EXC", "EXC")] = Expression(formula_ee)
        if formula_ei is not None:
            formulae[("EXC", "INH")] = Expression(formula_ei)
        if formula_ie is not None:
            formulae[("INH", "EXC")] = Expression(formula_ie)
        if formula_ii is not None:
            formulae[("INH", "INH")] = Expression(formula_ii)

        mtypes = get_mtypes_from_edge_population(circuit.edges[edge_population])

        if isinstance(sample, str):
            dset = read_nsyn(sample).set_index(["from", "to"])

            def estimate(pathway):
                return dset.loc[pathway]["mean"]

        else:
            if sample is None:
                sample = {}
            estimate = partial(
                _estimate_nsyn,
                circuit_config=circuit._circuit_config_path,
                population=edge_population,
                sample_size=sample.get("size", 100),
                pre=sample.get("pre", None),
                post=sample.get("post", None),
            )

        syn_class_map = _get_syn_class_map(circuit, edge_population)

        for pathway in itertools.product(mtypes, mtypes):
            yield Task(
                _execute, pathway, estimate, formulae, syn_class_map, max_value, task_group=__name__
            )


def _get_syn_class_map(circuit, edge_population):
    # TODO: a better way to get mtype -> synapse_class mapping (from the recipe directly?)
    dfs = []
    properties = [Cell.MTYPE, Cell.SYNAPSE_CLASS]
    edge_pop = circuit.edges[edge_population]

    for node_population in (edge_pop.source, edge_pop.target):
        if not set(properties) - node_population.property_names:
            dfs.append(node_population.get(properties=properties))

    if not dfs:
        raise ValueError("EMPTY LIST")  # TODO: change

    return dict(pd.concat(dfs).drop_duplicates().to_numpy())


def _execute(pathway, estimate, formulae, syn_class_map, max_value):
    value = estimate(pathway=pathway)
    if np.isnan(value):
        L.warning("Could not estimate '%s' nsyn, skipping", pathway)
        return []
    L.info("nsyn estimate for pathway %s: %.3g", pathway, value)
    value = _choose_formula(formulae, pathway, syn_class_map)(value)
    # NSETM-1137 consider nan as 1.0
    if value < 1.0 or np.isnan(value):
        value = 1.0
    if max_value is not None:
        value = min(value, max_value)
    return [(pathway, {MEAN_SYNS_CONNECTION: value})]
