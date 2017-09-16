"""
This strategy estimates the functional mean number of synapses per
connection from the structural number of appositions per connection.
For the prediction, an algebraic expression using 'n' (mean number of
appositions) can be specified as a string (see below).
"""

import itertools
import logging
import numpy as np
from functools import partial

from Equation import Expression
from bluepy.v2.enums import Cell

from bluerecipe.dataset import read_nsyn
from bluerecipe.params import MEAN_SYNS_CONNECTION


L = logging.getLogger(__name__)


def choose_formula(formulae, pathway, syn_class_map):
    """ Choose formula based on pre- and post- synapse class (EXC | INH). """
    custom = (syn_class_map[pathway[0]], syn_class_map[pathway[1]])
    if custom in formulae:
        return formulae[custom]
    else:
        return formulae[('*', '*')]


def estimate_nsyn(circuit, pathway, sample_size, sample_target):
    """ Mean nsyn for given mtype. """
    pre = {Cell.MTYPE: pathway[0]}
    post = {Cell.MTYPE: pathway[1]}
    if sample_target is not None:
        pre['$target'] = sample_target
        post['$target'] = sample_target
    values = circuit.v2.stats.sample_pathway_synapse_count(n=sample_size, pre=pre, post=post)
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

    mtypes = sorted(circuit.v2.cells.mtypes)

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
            sample_target=sample.get('target', None)
        )

    # TODO: a better way to get mtype -> synapse_class mapping (from the recipe directly?)
    syn_class_map = dict(
        circuit.v2.cells.get(properties=[Cell.MTYPE, Cell.SYNAPSE_CLASS]).drop_duplicates().values
    )

    result = {}
    for pathway in itertools.product(mtypes, mtypes):
        value = estimate(pathway=pathway)
        if np.isnan(value):
            L.warn("Could not estimate '%s' nsyn, skipping", pathway)
            continue
        L.debug("nsyn estimate for pathway %s: %.3g", pathway, value)
        value = choose_formula(formulae, pathway, syn_class_map)(value)
        if max_value is not None:
            value = min(value, max_value)
        result[pathway] = {
            MEAN_SYNS_CONNECTION: value
        }

    return result
