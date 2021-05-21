"""Calculating connectome stats."""

import itertools
import logging
import os

import neurom as nm
import numpy as np
from bluepy import Circuit, Segment, Synapse
from voxcell import ROIMask

from connectome_tools.utils import Task, run_parallel

L = logging.getLogger(__name__)


def _segment_lengths(segments):
    """Find segment lengths given a DataFrame returned by morph.spatial_index() query."""
    return np.linalg.norm(
        segments[[Segment.X1, Segment.Y1, Segment.Z1]].values
        - segments[[Segment.X2, Segment.Y2, Segment.Z2]].values,
        axis=1,
    )


def _load_mask(circuit, mask):
    if mask is None:
        return None
    else:
        return circuit.atlas.load_data(mask, cls=ROIMask)


def _calc_bouton_density(circuit, gid, projection, synapses_per_bouton, mask):
    """Calculate bouton density for a given `gid`."""
    if projection is None:
        conn_obj = circuit.connectome
    else:
        conn_obj = circuit.projection(projection)
    if mask is None:
        # count all efferent synapses and total axon length
        synapse_count = len(conn_obj.efferent_synapses(gid))
        axon_length = nm.get(
            "neurite_lengths", circuit.morph.get(gid, False), neurite_type=nm.AXON
        )[0]
    else:
        # find all segments which endpoints fall into the region of interest
        all_pts = circuit.morph.segment_points(gid, transform=True, neurite_type=nm.AXON)
        mask1 = mask.lookup(all_pts[[Segment.X1, Segment.Y1, Segment.Z1]].values, outer_value=False)
        mask2 = mask.lookup(all_pts[[Segment.X2, Segment.Y2, Segment.Z2]].values, outer_value=False)
        filtered = all_pts[mask1 & mask2]

        if filtered.empty:
            L.warning("No axon segments found inside region of interest for GID %d", gid)
            return np.nan

        # total length for those filtered segments
        axon_length = _segment_lengths(filtered).sum()

        # find axon segments with synapses; count synapses per each such segment
        INDEX_COLS = [Synapse.PRE_SECTION_ID, Synapse.PRE_SEGMENT_ID]
        syn_per_segment = (
            conn_obj.efferent_synapses(gid, properties=INDEX_COLS).groupby(INDEX_COLS).size()
        )

        # count synapses on filtered segments
        synapse_count = syn_per_segment.loc[
            syn_per_segment.index.intersection(filtered.index)
        ].sum()

    return (1.0 * synapse_count / synapses_per_bouton) / axon_length


def bouton_density(circuit, gid, projection=None, synapses_per_bouton=1.0, mask=None):
    """Calculate bouton density for a given `gid`."""
    mask = _load_mask(circuit, mask)
    return _calc_bouton_density(circuit, gid, projection, synapses_per_bouton, mask)


def sample_bouton_density(
    circuit, n, group=None, projection=None, synapses_per_bouton=1.0, mask=None, n_jobs=1
):
    """Sample bouton density.

    Args:
        circuit: circuit instance
        n: sample size
        group: cell group
        projection (str, default=None): Name of a projection. If specified, calculates bouton
            density based on synapses in that projection, and that projection only. By default
            (i.e. None) uses the local connectivity only.
        synapses_per_bouton: assumed number of synapses per bouton
        mask (str): region of interest mask
        n_jobs (int): number of parallel jobs (1 for single process, -1 to use all the cpus)

    Returns:
        numpy array of length min(n, N) with bouton density per cell,
        where N is the total number cells in the specified cell group.
    """
    gids = circuit.cells.ids(group)
    if len(gids) > n:
        gids = np.random.choice(gids, size=n, replace=False)
    elif len(gids) == 0:
        L.warning("No GID matching selection for group '%s'", group)
        return np.empty(0)
    if n_jobs == 1:
        return _sample_bouton_density_task(circuit, gids, projection, synapses_per_bouton, mask)
    else:
        return _sample_bouton_density_parallel(
            circuit, gids, projection, synapses_per_bouton, mask, n_jobs=n_jobs
        )


def _sample_bouton_density_task(
    circuit_or_config, gids, projection=None, synapses_per_bouton=1.0, mask=None
):
    """Sample bouton density task."""
    # If executed in a subprocess, a configuration should be passed instead of a circuit instance.
    if isinstance(circuit_or_config, Circuit):
        circuit = circuit_or_config
    else:
        circuit = Circuit(circuit_or_config)
    mask = _load_mask(circuit, mask)
    return np.array(
        [_calc_bouton_density(circuit, gid, projection, synapses_per_bouton, mask) for gid in gids]
    )


def _sample_bouton_density_parallel(
    circuit, gids, projection=None, synapses_per_bouton=1.0, mask=None, n_jobs=-1
):
    """Sample bouton density in parallel."""
    # The gids are split in chunks to reduce the number of tasks submitted to the subprocesses.
    n_chunks = n_jobs if n_jobs > 0 else os.cpu_count() or 1
    # minimum number of gids to be processed in a single job
    min_gids_per_job = int(os.getenv("MIN_GIDS_PER_JOB", "1"))
    n_chunks = min(n_chunks, len(gids) // min_gids_per_job)
    L.info(
        "Sampling bouton density using jobs=%s and splitting %s gids in %s chunks",
        n_jobs,
        len(gids),
        n_chunks,
    )
    tasks = [
        Task(
            _sample_bouton_density_task,
            circuit.config,
            chunk,
            projection=projection,
            synapses_per_bouton=synapses_per_bouton,
            mask=mask,
            task_group="sample_bouton_density",
        )
        for chunk in np.array_split(gids, n_chunks)
    ]
    # base_seed is None because the RNG is not used in the subprocesses
    results = run_parallel(tasks, n_jobs, base_seed=None)
    return np.concatenate([result.value for result in results])


def sample_pathway_synapse_count(
    circuit, n, pre=None, post=None, projection=None, unique_gids=False
):
    """Sample synapse count for pathway connections.

    Args:
        circuit: circuit instance
        n: sample size
        pre: presynaptic cell group
        post: postsynaptic cell group
        projection (str, default=None): Name of a projection. If specified, uses synapses in
            that projection only instead of the local connectivity.
        unique_gids(bool): don't use one GID more than once

    Returns:
        numpy array of length min(n, N) with synapse number per connection,
        where N is the total number of connections satisfying the constraints.
    """
    if projection is None:
        conn_obj = circuit.connectome
    else:
        conn_obj = circuit.projection(projection)
    it = conn_obj.iter_connections(
        pre, post, shuffle=True, unique_gids=unique_gids, return_synapse_count=True
    )
    return np.array([p[2] for p in itertools.islice(it, n)])
