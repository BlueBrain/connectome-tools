"""Calculate partial recipes and merge them in a single final recipe."""
import logging
from pathlib import Path

import click

from connectome_tools.merge import WORKDIR, CreateFullRecipe, delete_temporary_dirs
from connectome_tools.utils import (
    DIR_PATH,
    EXISTING_FILE_PATH,
    FILE_PATH,
    clean_slurm_env,
    runalone,
    setup_logging,
    timed,
)

L = logging.getLogger("s2f-recipe-merge")


@click.group()
@click.version_option()
def cli():
    """The CLI entry point."""


@cli.command()
@click.argument("circuit", type=EXISTING_FILE_PATH)
@click.option(
    "-c",
    "--config",
    required=True,
    help="Path to the merge config file (YAML)",
    type=EXISTING_FILE_PATH,
)
@click.option(
    "-e",
    "--executor-config",
    required=True,
    help="Path to the executor config file (YAML)",
    type=EXISTING_FILE_PATH,
)
@click.option("-o", "--output", required=True, help="Path to the output file (XML)", type=FILE_PATH)
@click.option(
    "-w",
    "--workdir",
    help="Path to the working directory",
    default=WORKDIR,
    type=DIR_PATH,
    show_default=True,
)
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
def run(circuit, config, executor_config, output, workdir, verbose, seed, jobs):
    """S2F recipe generation with tasks split and merged by region."""
    level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 2)]
    setup_logging(level=level)
    clean_slurm_env()
    with timed(L, "Recipe generation"):
        task = CreateFullRecipe(
            main_config=Path(config).resolve(),
            executor_config=Path(executor_config).resolve(),
            circuit_config=Path(circuit).resolve(),
            workdir=Path(workdir).resolve(),
            output=Path(output).resolve(),
            seed=seed,
            jobs=jobs,
            log_level=level,
        )
        task.run()


@cli.command()
@click.option(
    "-w",
    "--workdir",
    help="Path to the working directory to clean",
    default=WORKDIR,
    type=DIR_PATH,
    show_default=True,
)
@click.option("-v", "--verbose", count=True, help="-v for INFO, -vv for DEBUG")
@runalone
def clean(workdir, verbose):
    """Delete all the partial recipes and slurm logs."""
    level = (logging.WARNING, logging.INFO, logging.DEBUG)[min(verbose, 2)]
    setup_logging(level=level)
    delete_temporary_dirs(Path(workdir).resolve())
