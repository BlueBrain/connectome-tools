""" This strategy takes parameters from already existing S2F recipe. """
from functools import partial

import lxml.etree as ET


def prepare(_, recipe_path):
    # pylint: disable=missing-docstring
    yield partial(_worker, recipe_path)


def _worker(recipe_path):
    # pylint: disable=missing-docstring
    tree = ET.parse(recipe_path)
    return [
        (
            (elem.attrib.pop("from"), elem.attrib.pop("to")),
            {k: float(v) for k, v in elem.attrib.iteritems()},
        )
        for elem in tree.findall("mTypeRule")
    ]
