""" This strategy takes parameters from already existing S2F recipe. """

import lxml.etree as ET


def execute(circuit, recipe_path):
    # pylint: disable=missing-docstring,unused-argument
    result = {}
    tree = ET.parse(recipe_path)
    for elem in tree.findall('mTypeRule'):
        pathway = elem.attrib.pop('from'), elem.attrib.pop('to')
        result[pathway] = {
            k: float(v) for k, v in elem.attrib.iteritems()
        }
    return result
