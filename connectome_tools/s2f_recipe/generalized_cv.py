"""
This strategy uses a generalized value of the coefficient
of variation of the number of synapses per connection.
"""

from connectome_tools.s2f_recipe import CV_SYNS_CONNECTION


def execute(_, cv):
    # pylint: disable=missing-docstring
    return {
        ('*', '*'): {CV_SYNS_CONNECTION: cv}
    }
