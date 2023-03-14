"""Connectome statistics."""

import itertools
import logging

import click
import numpy as np
from bluepy import Circuit

from connectome_tools import stats
from connectome_tools.utils import cell_group, runalone

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
@click.option("-n", "--sample-size", type=int, default=100, help="Sample size", show_default=True)
@click.option("--pre", default=None, help="Presynaptic target", show_default=True)
@click.option("--post", default=None, help="Postsynaptic target", show_default=True)
@click.option("--projection", default=None, help="Projection name", show_default=True)
@click.option("--short", is_flag=True, default=False, help="Omit sampled values", show_default=True)
def nsyn_per_connection(circuit, sample_size, pre, post, projection, short):
    """Mean connection synapse count per pathway."""
    circuit = Circuit(circuit)
    mtypes = sorted(circuit.cells.mtypes)

    click.echo("\t".join(["from", "to", "mean", "std", "size", "sample"]))

    for pre_mtype, post_mtype in itertools.product(mtypes, mtypes):
        sample = stats.sample_pathway_synapse_count(
            circuit,
            n=sample_size,
            pre=cell_group(pre_mtype, target=pre),
            post=cell_group(post_mtype, target=post),
            projection=projection,
        )
        mean, std, size, values = _format_sample(sample, short)
        click.echo("\t".join([pre_mtype, post_mtype, mean, std, size, values]))


@app.command()
@click.argument("circuit")
@click.option("-n", "--sample-size", type=int, default=100, help="Sample size", show_default=True)
@click.option("-t", "--sample-target", default=None, help="Sample target", show_default=True)
@click.option("--mask", default=None, help="Region of interest", show_default=True)
@click.option(
    "--assume-syns-bouton",
    type=float,
    default=1.0,
    help="Synapse count per bouton",
    show_default=True,
)
@click.option("--projection", default=None, help="Projection name", show_default=True)
@click.option("--short", is_flag=True, default=False, help="Omit sampled values", show_default=True)
def bouton_density(
    circuit, sample_size, sample_target, mask, assume_syns_bouton, projection, short
):
    """Mean bouton density per mtype."""
    circuit = Circuit(circuit)
    mtypes = sorted(circuit.cells.mtypes)

    click.echo("\t".join(["mtype", "mean", "std", "size", "sample"]))

    for mtype in itertools.chain(["*"], mtypes):
        if mtype == "*":
            group = sample_target
        else:
            group = cell_group(mtype, target=sample_target)
        sample = stats.sample_bouton_density(
            circuit,
            n=sample_size,
            group=group,
            mask=mask,
            synapses_per_bouton=assume_syns_bouton,
            projection=projection,
        )
        mean, std, size, values = _format_sample(sample, short)
        click.echo("\t".join([mtype, mean, std, size, values]))
