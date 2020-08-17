""" This strategy takes parameters from already existing S2F recipe. """

import lxml.etree as ET

from connectome_tools.s2f_recipe.utils import Task


def prepare(_, recipe_path):
    # pylint: disable=missing-docstring
    yield Task(_execute, recipe_path, task_group=__name__)


def _execute(recipe_path):
    # pylint: disable=missing-docstring
    tree = ET.parse(recipe_path)
    return [
        (
            (elem.attrib.pop("from"), elem.attrib.pop("to")),
            {k: float(v) for k, v in elem.attrib.iteritems()},
        )
        for elem in tree.findall("mTypeRule")
    ]
