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
    # The parser is backward compatible, but it will break if both the old and the new formats
    # are used in the same file, because the final order of the rules could be different.
    # At the moment, it will break also if the rules in the new format contain selection attributes
    # different from fromMType/toMType (e.g. fromEType/toEType, fromRegion/toRegion...).
    tree = ET.parse(recipe_path)
    # old format (circuit-documentation 0.0.19)
    old_rules = [
        (
            (elem.attrib.pop("from"), elem.attrib.pop("to")),
            {k: float(v) for k, v in elem.attrib.iteritems()},
        )
        for elem in tree.findall("mTypeRule")
    ]
    # new format (circuit-documentation 0.0.20)
    new_rules = [
        (
            (elem.attrib.pop("fromMType"), elem.attrib.pop("toMType")),
            {k: float(v) for k, v in elem.attrib.iteritems()},
        )
        for elem in tree.findall("rule")
    ]
    if new_rules and old_rules:
        raise ValueError("Rules in different formats cannot be used in the same file")
    return new_rules or old_rules
