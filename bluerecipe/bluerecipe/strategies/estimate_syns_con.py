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


def execute(circuit, formula, sample_size=100, sample_target=None, max_value=None):
    # pylint: disable=missing-docstring
    formula = Expression(formula)
    mtypes = sorted(circuit.v2.stats.mtypes)

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
        estimate = formula(synapse_number)
        if max_value:
            estimate = min(estimate, max_value)
        result[pathway] = {
            MEAN_SYNS_CONNECTION: estimate
        }

    return result
