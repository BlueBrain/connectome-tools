"""
This strategy uses a generalized value of the coefficient
of variation of the number of synapses per connection.
"""

from bluerecipe.params import CV_SYNS_CONNECTION


def execute(circuit, cv):
    # pylint: disable=missing-docstring,unused-argument
    return {
        ('*', '*'): {CV_SYNS_CONNECTION: cv}
    }
