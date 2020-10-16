"""Strategy override_mtype.

This strategy is to be used last and overrides parameters for a subset of mtypes.
This is meant to avoid excessive pruning that would otherwise
happen due to the special nature of ChC synapses on the axon.
(more precisely: one touch actually represents a train of 5 synapses
and therefore the syns per con calculation would be off by that factor).
"""

from connectome_tools.s2f_recipe.utils import Task


def prepare(circuit, mtype_pattern, **kwargs):
    # noqa: D103 # pylint: disable=missing-docstring
    yield Task(_execute, circuit.cells.mtypes, mtype_pattern, task_group=__name__, **kwargs)


def _execute(mtypes, mtype_pattern, **kwargs):
    return [((mtype, "*"), kwargs) for mtype in mtypes if mtype_pattern in mtype]
