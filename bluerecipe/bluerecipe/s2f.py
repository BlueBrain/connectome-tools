""" S2F recipe generation. """

import itertools
import logging
import lxml.etree as ET

from collections import OrderedDict

from bluerecipe.params import (
    BOUTON_REDUCTION_FACTOR,
    CV_SYNS_CONNECTION,
    MEAN_SYNS_CONNECTION,
)
from bluerecipe.strategies import (
    estimate_bouton_reduction,
    estimate_individual_bouton_reduction,
    estimate_syns_con,
    existing_recipe,
    experimental_syns_con,
    generalized_cv,
)


L = logging.getLogger('s2f_recipe')

REQUIRED_PARAMS = [
    BOUTON_REDUCTION_FACTOR,
    CV_SYNS_CONNECTION,
    MEAN_SYNS_CONNECTION,
]

DISPATCH = {
    'estimate_bouton_reduction': estimate_bouton_reduction,
    'estimate_individual_bouton_reduction': estimate_individual_bouton_reduction,
    'estimate_syns_con': estimate_syns_con,
    'experimental_syns_con': experimental_syns_con,
    'existing_recipe': existing_recipe,
    'generalized_cv': generalized_cv,
}


def generate_recipe(circuit, strategies):
    """ Generate S2F recipe for `circuit` using `strategies`. """
    result = {}
    mtypes = circuit.v2.cells.mtypes
    for entry in strategies:
        assert len(entry) == 1
        strategy, kwargs = entry.items()[0]
        L.info("Executing strategy '%s'...", strategy)
        strategy_result = DISPATCH[strategy].execute(circuit, **kwargs)
        for pathway_wildcard, params in strategy_result.iteritems():
            pathways = itertools.product(
                mtypes if pathway_wildcard[0] == '*' else [pathway_wildcard[0]],
                mtypes if pathway_wildcard[1] == '*' else [pathway_wildcard[1]]
            )
            for pathway in pathways:
                result.setdefault(pathway, {}).update(params)
    return result


def write_recipe(output_path, recipe, comment=None):
    """ Dump `recipe` as XML to `output_path`. """
    root = ET.Element('ConnectionRules')
    if comment is not None:
        root.addprevious(ET.Comment(comment))
    for pathway, params in sorted(recipe.iteritems()):
        attr = OrderedDict()
        attr['from'] = pathway[0]
        attr['to'] = pathway[1]
        for param, value in params.iteritems():
            attr[param] = "{:.3f}".format(value)
        ET.SubElement(root, 'mTypeRule', attr)

    tree = ET.ElementTree(root)
    with open(output_path, 'w') as f:
        tree.write(f, pretty_print=True, xml_declaration=True, encoding='utf-8')


def verify_recipe(circuit, recipe):
    """ Check that all the entries in the recipe have all required parameters. """
    for pathway, params in recipe.iteritems():
        undefined_params = set(REQUIRED_PARAMS) - set(params)
        if undefined_params:
            raise RuntimeError(
                "pathway {} has undefined parameters: {}".format(
                    pathway, ", ".join(undefined_params)
                )
            )

    mtypes = circuit.v2.cells.mtypes
    missing_pathways = set(itertools.product(mtypes, mtypes)) - set(recipe.keys())
    if missing_pathways:
        L.warning("Undefined pathways: %s", ", ".join(map(str, missing_pathways)))
