"""
This strategy is to be used last and overrides parameters for a subset of mtypes.
This is meant to avoid excessive pruning that would otherwise
happen due to the special nature of ChC synapses on the axon.
(more precisely: one touch actually represents a train of 5 synapses
and therefore the syns per con calculation would be off by that factor).
"""


def execute(circuit, mtype_pattern, **kwargs):
    # pylint: disable=missing-docstring
    return {
        (mtype, '*'): kwargs
        for mtype in circuit.v2.cells.mtypes
        if mtype_pattern in mtype
    }
