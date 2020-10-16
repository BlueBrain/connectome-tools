"""Strategy generalized_cv.

This strategy uses a generalized value of the coefficient
of variation of the number of synapses per connection.
"""

from connectome_tools.s2f_recipe import CV_SYNS_CONNECTION
from connectome_tools.s2f_recipe.utils import Task


def prepare(_, cv):
    # noqa: D103 # pylint: disable=missing-docstring
    yield Task(_execute, cv, task_group=__name__)


def _execute(cv):
    return [(("*", "*"), {CV_SYNS_CONNECTION: cv})]
