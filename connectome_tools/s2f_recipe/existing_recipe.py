"""Strategy existing_recipe.

This strategy takes parameters from already existing S2F recipe.
"""

import lxml.etree as ET

from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.utils import Task


class Executor(BaseExecutor):
    """Executor class for existing_recipe strategy."""

    is_parallel = False

    def prepare(self, _, recipe_path):
        """Yield tasks that should be executed.

        Args:
            recipe_path (str): path to the existing xml recipe to be imported.

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ
        yield Task(_execute, recipe_path, task_group=__name__)


def _execute(recipe_path):
    tree = ET.parse(recipe_path)
    return [
        (
            (elem.attrib.pop("from"), elem.attrib.pop("to")),
            {k: float(v) for k, v in elem.attrib.iteritems()},
        )
        for elem in tree.findall("mTypeRule")
    ]
