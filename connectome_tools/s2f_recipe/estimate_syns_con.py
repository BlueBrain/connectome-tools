"""
This strategy estimates the functional mean number of synapses per
connection from the structural number of appositions per connection.
For the prediction, an algebraic expression using 'n' (mean number of
appositions) can be specified as a string (see below).
"""

import itertools
import logging

from functools import partial

import numpy as np

from Equation import Expression
from bluepy.v2 import Cell

from connectome_tools.dataset import read_nsyn
from connectome_tools.s2f_recipe import MEAN_SYNS_CONNECTION
from connectome_tools.stats import sample_pathway_synapse_count


L = logging.getLogger(__name__)


def choose_formula(formulae, pathway, syn_class_map):
    """ Choose formula based on pre- and post- synapse class (EXC | INH). """
    custom = (syn_class_map[pathway[0]], syn_class_map[pathway[1]])
    if custom in formulae:
        return formulae[custom]
    else:
        return formulae[('*', '*')]


def _cell_group(mtype, target=None):
    result = {Cell.MTYPE: mtype}
    if target is not None:
        result['$target'] = target
    return result


def estimate_nsyn(circuit, pathway, sample_size, pre, post):
    """ Mean nsyn for given mtype. """
    pre_mtype, post_mtype = pathway
    values = sample_pathway_synapse_count(
        circuit,
        n=sample_size,
        pre=_cell_group(pre_mtype, target=pre),
        post=_cell_group(post_mtype, target=post)
    )
    return values.mean()


def execute(
    circuit,
    formula, formula_ee=None, formula_ei=None, formula_ie=None, formula_ii=None, max_value=None,
    sample=None
):
    # pylint: disable=missing-docstring, too-many-arguments, too-many-locals
    formulae = {}
    formulae[('*', '*')] = Expression(formula)
    if formula_ee is not None:
        formulae[('EXC', 'EXC')] = Expression(formula_ee)
    if formula_ei is not None:
        formulae[('EXC', 'INH')] = Expression(formula_ei)
    if formula_ie is not None:
        formulae[('INH', 'EXC')] = Expression(formula_ie)
    if formula_ii is not None:
        formulae[('INH', 'INH')] = Expression(formula_ii)

    mtypes = sorted(circuit.cells.mtypes)

    if isinstance(sample, str):
        dset = read_nsyn(sample).set_index(['from', 'to'])
        estimate = lambda pathway: dset.loc[pathway]['mean']
    else:
        if sample is None:
            sample = {}
        estimate = partial(
            estimate_nsyn,
            circuit=circuit,
            sample_size=sample.get('size', 100),
            pre=sample.get('pre', None),
            post=sample.get('post', None)
        )

    # TODO: a better way to get mtype -> synapse_class mapping (from the recipe directly?)
    syn_class_map = dict(
        circuit.cells.get(properties=[Cell.MTYPE, Cell.SYNAPSE_CLASS]).drop_duplicates().values
    )

    result = {}
    for pathway in itertools.product(mtypes, mtypes):
        value = estimate(pathway=pathway)
        if np.isnan(value):
            L.warning("Could not estimate '%s' nsyn, skipping", pathway)
            continue
        L.debug("nsyn estimate for pathway %s: %.3g", pathway, value)
        value = choose_formula(formulae, pathway, syn_class_map)(value)
        value = max(value, 1.0)
        if max_value is not None:
            value = min(value, max_value)
        result[pathway] = {
            MEAN_SYNS_CONNECTION: value
        }

    return result
