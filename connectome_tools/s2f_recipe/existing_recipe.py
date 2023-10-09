"""Strategy existing_recipe.

This strategy takes parameters from already existing S2F recipe.
"""
import logging
from collections import Counter

import lxml.etree as ET

from connectome_tools.s2f_recipe.utils import BaseExecutor
from connectome_tools.utils import Task

L = logging.getLogger(__name__)


class Executor(BaseExecutor):
    """Executor class for existing_recipe strategy."""

    is_parallel = False

    def prepare(self, _, __, recipe_path):
        """Yield tasks that should be executed.

        Args:
            recipe_path (str): path to the existing xml recipe to be imported.

        Yields:
            (Task) task to be executed.
        """
        # pylint: disable=arguments-differ
        yield Task(_execute, recipe_path, task_group=__name__)


def _load_old_rules(tree):
    """Load rules in the old format (circuit-documentation 0.0.19)."""
    return [
        # the values read will be saved unchanged to the final recipe
        ((elem.attrib.pop("from"), elem.attrib.pop("to")), dict(elem.attrib))
        for elem in tree.findall("mTypeRule")
    ]


def _load_new_rules(tree):
    """Load rules in the new format (circuit-documentation 0.0.20)."""
    return [
        # the values read will be saved unchanged to the final recipe
        ((elem.attrib.pop("fromMType"), elem.attrib.pop("toMType")), dict(elem.attrib))
        for elem in tree.findall("rule")
    ]


def _is_unique(rules):
    counter = Counter(pathway for pathway, params in rules)
    if len(counter) != len(rules):
        duplicates = sorted(pathway for pathway, count in counter.items() if count > 1)
        L.warning("Rules using the same pathway: %s", duplicates)
        return False
    return True


def _execute(recipe_path):
    """Return the rules read from an existing recipe."""
    # The parser is backward compatible, but it will raise an exception:
    # - if both the old and the new formats are used in the same file, because the order
    #   of the resulting rules is not granted to be the same
    # - if multiple rules with the same pathway exists, because they would be merged together,
    #   regardless of any other selection attribute (e.g. fromRegion/toRegion...)
    tree = ET.parse(recipe_path)
    old_rules = _load_old_rules(tree)
    new_rules = _load_new_rules(tree)
    if new_rules and old_rules:
        raise ValueError("Rules in different formats in the same file cannot be imported")
    if not _is_unique(old_rules) or not _is_unique(new_rules):
        raise ValueError("Rules using the same pathway cannot be imported")
    return new_rules or old_rules
