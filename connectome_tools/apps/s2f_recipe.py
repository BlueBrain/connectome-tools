#!/usr/bin/env python

"""S2F recipe generation."""

import itertools
import logging
from collections import OrderedDict

import click
import lxml.etree as ET
import numpy as np
import yaml
from bluepy import Circuit

from connectome_tools.s2f_recipe import (
    BOUTON_REDUCTION_FACTOR,
    CV_SYNS_CONNECTION,
    MEAN_SYNS_CONNECTION,
    P_A,
    PMU_A,
    estimate_bouton_reduction,
    estimate_individual_bouton_reduction,
    estimate_syns_con,
    existing_recipe,
    experimental_syns_con,
    generalized_cv,
    override_mtype,
)
from connectome_tools.utils import runalone, setup_logging, timed
from connectome_tools.version import __version__

L = logging.getLogger("s2f-recipe")

REQUIRED_PARAMS = {
    BOUTON_REDUCTION_FACTOR,
}
# other required params (first choice)
ALTERNATIVE_PARAMS_1 = {
    P_A,
    PMU_A,
}
# other required params (second choice)
ALTERNATIVE_PARAMS_2 = {
    CV_SYNS_CONNECTION,
    MEAN_SYNS_CONNECTION,
}

# Associate the right class for each strategy defined in the configuration.
DISPATCH = {
    "estimate_bouton_reduction": estimate_bouton_reduction.Executor,
    "estimate_individual_bouton_reduction": estimate_individual_bouton_reduction.Executor,
    "estimate_syns_con": estimate_syns_con.Executor,
    "experimental_syns_con": experimental_syns_con.Executor,
    "existing_recipe": existing_recipe.Executor,
    "generalized_cv": generalized_cv.Executor,
    "override_mtype": override_mtype.Executor,
}


def load_yaml(filepath):
    """Load YAML file."""
    with open(filepath) as f:
        return yaml.safe_load(f)


def validate_params(pathway_dict):
    """Validate and potentially remove unwanted parameters for a given pathway dict.

    Args:
        pathway_dict (dict): dictionary of parameters.

    Returns:
        (bool, set):
            True if successful, False otherwise.
            Set of missing parameters, or None if no required parameters are missing.
    """
    if not REQUIRED_PARAMS.issubset(pathway_dict):
        # required parameters are incomplete
        return False, REQUIRED_PARAMS.difference(pathway_dict)
    elif ALTERNATIVE_PARAMS_1.issubset(pathway_dict):
        # alternative_1 parameters are complete
        for k in ALTERNATIVE_PARAMS_2:
            # remove the unwanted alternative_2 parameters if they exist
            pathway_dict.pop(k, None)
        return True, None
    elif ALTERNATIVE_PARAMS_1.intersection(pathway_dict):
        # alternative_1 parameters are present but incomplete
        return False, ALTERNATIVE_PARAMS_1.difference(pathway_dict)
    elif ALTERNATIVE_PARAMS_2.issubset(pathway_dict):
        # alternative_2 parameters are complete
        return True, None
    else:
        # alternative_2 parameters are incomplete
        return False, ALTERNATIVE_PARAMS_2.difference(pathway_dict)


def execute_strategies(circuit, strategies, jobs, base_seed):
    """Execute each strategy sequentially."""
    strategy_results = []
    for entry in strategies:
        assert len(entry) == 1
        strategy, kwargs = next(iter(entry.items()))
        executor = DISPATCH[strategy](jobs, base_seed)
        results = executor.run(circuit, **kwargs)
        strategy_results.extend(results)
    return strategy_results


def init_recipe(task_results, mtypes):
    """Return the recipe assembled using the tasks results."""
    recipe = {}
    # task_results is a list of task results, one for each task
    for task_result in task_results:
        # each task_result contains a list of tuples (pathway_wildcard, params)
        # that are assembled in order (latter parameters can override former parameters)
        for pathway_wildcard, params in task_result.value:
            pathways = itertools.product(
                mtypes if pathway_wildcard[0] == "*" else [pathway_wildcard[0]],
                mtypes if pathway_wildcard[1] == "*" else [pathway_wildcard[1]],
            )
            for pathway in pathways:
                recipe.setdefault(pathway, {}).update(params)
    return recipe


def clean_recipe(recipe, mtypes):
    """Clean the recipe removing invalid pathways and unwanted parameters."""
    for pathway in itertools.product(mtypes, mtypes):
        if pathway not in recipe:
            L.warning("Undefined pathway: %s", pathway)
            continue
        is_valid, missing_params = validate_params(recipe[pathway])
        if not is_valid:
            L.warning(
                "pathway %s has undefined parameters: %s; skipping",
                pathway,
                ", ".join(missing_params),
            )
            del recipe[pathway]


def generate_recipe(circuit, strategies, jobs, base_seed):
    """Generate S2F recipe for `circuit` using `strategies`.

    Args:
        circuit: BluePy Circuit
        strategies: List of dictionaries, each one representing a strategy.
            Example of a single strategy::
            {
                "estimate_syns_con": {
                    "formula": "6 * ((n - 1) ** 0.5) - 1",
                    "formula_ee": "1.5 * n",
                    "max_value": 25.0,
                    "sample": {
                    "size": 1000
                    }
                }
            }
        jobs: Maximum number of concurrently running jobs. If -1 all CPUs are used.
            If 1 is given, no parallel computing code is used at all.
            For n_jobs below -1, (n_cpus + 1 + n_jobs) are used.
        base_seed: Base seed used to initialize the seed in the subprocesses.

    Returns:
        The recipe generated, i.e. a dictionary containing (pre_mtype, post_mtype) as key,
        and a dictionary of parameters as value.
    """
    mtypes = sorted(circuit.cells.mtypes)

    L.info("Execute strategies")
    task_results = execute_strategies(circuit, strategies, jobs=jobs, base_seed=base_seed)

    L.info("Assemble the recipe")
    recipe = init_recipe(task_results, mtypes)
    L.info("Clean the recipe")
    clean_recipe(recipe, mtypes)

    return recipe


def write_recipe(output_path, recipe, comment=None):
    """Dump `recipe` as XML to `output_path`."""
    root = ET.Element("ConnectionRules")
    if comment is not None:
        root.addprevious(ET.Comment(comment))
    for pathway, params in sorted(recipe.items()):
        attr = OrderedDict()
        attr["from"] = pathway[0]
        attr["to"] = pathway[1]
        for param, value in params.items():
            attr[param] = "{:.3f}".format(value)
        ET.SubElement(root, "mTypeRule", attr)

    tree = ET.ElementTree(root)
    with open(output_path, "wb") as f:
        tree.write(f, pretty_print=True, xml_declaration=True, encoding="utf-8")


@click.command()
@click.argument("circuit")
@click.option("-s", "--strategies", required=True, help="Path to strategies config (YAML)")
@click.option("-o", "--output", required=True, help="Path to output file (XML)")
@click.option("-v", "--verbose", count=True, help="-v for INFO, -vv for DEBUG")
@click.option("--seed", type=int, default=0, help="Pseudo-random generator seed", show_default=True)
@click.option(
    "-j",
    "--jobs",
    type=int,
    default=-1,
    help="Maximum number of concurrently running jobs (if -1 all CPUs are used)",
    show_default=True,
)
@runalone
def app(circuit, strategies, output, verbose, seed, jobs):  # noqa: D301
    """S2F recipe generation.

    See the official documentation for more information
    and for an example of a sbatch script to run the program.

    \f
    # Ignore Missing parameter(s) in Docstring with darglint
    # noqa: DAR101
    """
    level = {0: logging.WARN, 1: logging.INFO, 2: logging.DEBUG}[verbose]
    setup_logging(level=level)
    L.info("Configuration: circuit=%s, seed=%s, jobs=%s", circuit, seed, jobs)
    strategies = load_yaml(strategies)

    comment = (
        "\nGenerated by s2f-recipe=={version}"
        "\nfrom circuit {circuit}"
        "\nusing strategies (seed={seed}):"
        "\n{strategies}"
    ).format(version=__version__, circuit=circuit, seed=seed, strategies=yaml.dump(strategies))

    np.random.seed(seed)

    with timed(L, "Recipe generation"):
        circuit = Circuit(circuit)
        recipe = generate_recipe(circuit, strategies, jobs, base_seed=seed)
        write_recipe(output, recipe, comment=comment)
