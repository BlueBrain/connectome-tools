"""Connectome statistics."""

import itertools
import logging

import click
import numpy as np
from bluepysnap import Circuit

from connectome_tools import stats
from connectome_tools.utils import cell_group, get_node_population_mtypes, runalone

L = logging.getLogger(__name__)

NA_VALUE = "N/A"


def _format_sample(sample, short=False):
    """Get string representation for sample and its mean / std / size."""

    def ftoa(x):
        return f"{x:.3g}"

    size = len(sample)
    if size > 0:
        if short:
            values = NA_VALUE
        else:
            values = ",".join(map(ftoa, np.sort(sample)))
        return ftoa(np.nanmean(sample)), ftoa(np.nanstd(sample)), str(size), values
    else:
        return NA_VALUE, NA_VALUE, NA_VALUE, NA_VALUE


@click.group()
@click.version_option()
@click.option("--seed", type=int, default=0, help="Random generator seed", show_default=True)
@runalone
def app(seed):
    """Calculate some connectome statistics."""
    logging.basicConfig(level=logging.WARN)
    np.random.seed(seed)


@app.command()
@click.argument("circuit")
@click.option("-p", "--edge-population", required=True, help="Edge population name")
@click.option("-n", "--sample-size", type=int, default=100, help="Sample size", show_default=True)
@click.option("--pre", default=None, help="Presynaptic node set", show_default=True)
@click.option("--post", default=None, help="Postsynaptic node set", show_default=True)
@click.option("--short", is_flag=True, default=False, help="Omit sampled values", show_default=True)
def nsyn_per_connection(circuit, edge_population, sample_size, pre, post, short):
    """Mean connection synapse count per pathway."""
    edge_population = Circuit(circuit).edges[edge_population]
    pre_mtypes = get_node_population_mtypes(edge_population.source)
    post_mtypes = get_node_population_mtypes(edge_population.target)

    click.echo("\t".join(["from", "to", "mean", "std", "size", "sample"]))

    for pre_mtype, post_mtype in itertools.product(pre_mtypes, post_mtypes):
        sample = stats.sample_pathway_synapse_count(
            edge_population,
            n=sample_size,
            pre=cell_group(pre_mtype, node_set=pre),
            post=cell_group(post_mtype, node_set=post),
        )
        mean, std, size, values = _format_sample(sample, short)
        click.echo("\t".join([pre_mtype, post_mtype, mean, std, size, values]))


@app.command()
@click.argument("circuit")
@click.option("-p", "--edge-population", required=True, help="Edge population name")
@click.option(
    "-a", "--atlas", "atlas_path", default=None, help="Circuit atlas path", show_default=True
)
@click.option("-n", "--sample-size", type=int, default=100, help="Sample size", show_default=True)
@click.option("-t", "--node-set", default=None, help="Sample node set", show_default=True)
@click.option("--mask", default=None, help="Region of interest", show_default=True)
@click.option(
    "--assume-syns-bouton",
    type=float,
    default=1.0,
    help="Synapse count per bouton",
    show_default=True,
)
@click.option("--short", is_flag=True, default=False, help="Omit sampled values", show_default=True)
def bouton_density(
    circuit,
    edge_population,
    atlas_path,
    sample_size,
    node_set,
    mask,
    assume_syns_bouton,
    short,
):  # pylint: disable = too-many-locals
    """Mean bouton density per mtype."""
    edge_population = Circuit(circuit).edges[edge_population]
    mtypes = get_node_population_mtypes(edge_population.source)

    click.echo("\t".join(["mtype", "mean", "std", "size", "sample"]))

    for mtype in itertools.chain(["*"], mtypes):
        if mtype == "*":
            group = node_set
        else:
            group = cell_group(mtype, node_set=node_set)
        sample = stats.sample_bouton_density(
            edge_population,
            n=sample_size,
            group=group,
            synapses_per_bouton=assume_syns_bouton,
            mask=mask,
            atlas_path=atlas_path,
        )
        mean, std, size, values = _format_sample(sample, short)
        click.echo("\t".join([mtype, mean, std, size, values]))
