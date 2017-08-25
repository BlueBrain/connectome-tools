"""
This strategy estimates the functional mean number of synapses per
connection from the structural number of appositions per connection.
For the prediction, an algebraic expression using 'n' (mean number of
appositions) can be specified as a string (see below).
"""

import itertools
import logging

from Equation import Expression
from bluepy.v2.enums import Cell

from bluerecipe.params import MEAN_SYNS_CONNECTION


L = logging.getLogger('s2f_recipe')


def choose_formula(formulae, pathway, syn_class_map):
    """ Choose formula based on pre- and post- synapse class (EXC | INH). """
    custom = (syn_class_map[pathway[0]], syn_class_map[pathway[1]])
    if custom in formulae:
        return formulae[custom]
    else:
        return formulae[('*', '*')]


def execute(
    circuit,
    formula, formula_ee=None, formula_ei=None, formula_ie=None, formula_ii=None,
    sample_size=100, sample_target=None, max_value=None
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

    # TODO: a better way to get mtype -> synapse_class mapping (from the recipe directly?)
    syn_class_map = dict(
        circuit.v2.cells.get(properties=[Cell.MTYPE, Cell.SYNAPSE_CLASS]).drop_duplicates().values
    )

    result = {}
    for pathway in itertools.product(mtypes, mtypes):
        pre = {Cell.MTYPE: pathway[0]}
        post = {Cell.MTYPE: pathway[1]}
        if sample_target is not None:
            pre['$target'] = sample_target
            post['$target'] = sample_target
        sample = circuit.v2.stats.sample_pathway_synapse_count(n=sample_size, pre=pre, post=post)
        if len(sample) > 0:
            synapse_number = sample.mean()
            L.debug(
                "Sample synapse number for pathway %s sample: %.3g",
                pathway, synapse_number
            )
        else:
            synapse_number = 2.0
            L.warn(
                "No connection found for pathway %s, using %.3g as sample synapse number (??)",
                pathway, synapse_number
            )
        estimate = choose_formula(formulae, pathway, syn_class_map)(synapse_number)
        if max_value:
            estimate = min(estimate, max_value)
        result[pathway] = {
            MEAN_SYNS_CONNECTION: estimate
        }

    return result
