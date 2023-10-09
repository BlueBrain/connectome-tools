"""Calculating connectome stats."""

import itertools
import logging
import os

import numpy as np
import pandas as pd
from morphio import SectionType
from voxcell import ROIMask
from voxcell.nexus.voxelbrain import Atlas

from connectome_tools.utils import Task, run_parallel

L = logging.getLogger(__name__)


PRE_SECTION_ID = "efferent_section_id"
PRE_SEGMENT_ID = "efferent_segment_id"


SECTION_ID = "section_id"
SEGMENT_ID = "segment_id"


SEGMENT_START_COLS = ["x1", "y1", "z1"]
SEGMENT_END_COLS = ["x2", "y2", "z2"]


def _segment_lengths(segments):
    """Find segment lengths given a DataFrame returned by morph.spatial_index() query."""
    return np.linalg.norm(
        segments[SEGMENT_START_COLS].values - segments[SEGMENT_END_COLS].values, axis=1
    )


def _segment_points(morph, neurite_type=None):
    """Get segment points for given `morph`.

    Args:
        morph: morph of interest
        neurite_type (morphio.SectionType): neurite type of interest

    Returns:
        pandas DataFrame multi-indexed by (SECTION_ID, SEGMENT_ID);
        and SEGMENT_START_COLS and SEGMENT_END_COLS as columns.

    Note: soma is returned as a spherical segment
    """
    index = []
    chunks = []
    if neurite_type is None:
        it = morph.iter()
    else:
        it = (x for x in morph.iter() if x.type == neurite_type)

    for sec in it:
        pts = sec.points
        chunk = np.zeros((len(pts) - 1, 6))
        chunk[:, 0:3] = pts[:-1]
        chunk[:, 3:6] = pts[1:]
        chunks.append(chunk)

        # MorphIO doesn't consider the soma a section; makes sure we match the
        # section ids from the edge file
        index.extend((sec.id + 1, seg_id) for seg_id in range(len(pts) - 1))

    # MorphIO doesn't consider the soma as as segment, manually make a spherical one
    if morph.soma and neurite_type in (None, SectionType.all, SectionType.soma):
        index.append((0, 0))
        chunk = np.concatenate((morph.soma.center, morph.soma.center))[np.newaxis]
        chunks.append(chunk)

    if index:
        result = pd.DataFrame(
            data=np.concatenate(chunks),
            index=pd.MultiIndex.from_tuples(index, names=[SECTION_ID, SEGMENT_ID]),
            columns=[*SEGMENT_START_COLS, *SEGMENT_END_COLS],
        )
    else:
        # no sections with specified neurite type
        result = pd.DataFrame()

    return result


def _load_mask(mask):
    if mask is None:
        return None
    else:
        atlas = Atlas.open("/gpfs/bbp.cscs.ch/project/proj55/iavarone/releases/atlases/O1-323/")
        return atlas.load_data(mask, cls=ROIMask)
        # raise NotImplementedError("Atlas method not implemented yet")


def _calc_bouton_density(edge_population, gid, synapses_per_bouton, mask):
    """Calculate bouton density for a given `gid`."""
    # pylint: disable=too-many-locals
    if mask is None:
        # count all efferent synapses and total axon length
        synapse_count = len(edge_population.efferent_edges(gid))
        # total length of the segments
        all_pts = _segment_points(
            edge_population.source.morph.get(gid, transform=False, extension="h5"),
            neurite_type=SectionType.axon,
        )
        axon_length = _segment_lengths(all_pts).sum()

    else:
        # Find all segments which endpoints fall into the region of interest.
        all_pts = _segment_points(
            edge_population.source.morph.get(gid, transform=True, extension="h5"),
            neurite_type=SectionType.axon,
        )
        mask1 = mask.lookup(all_pts[SEGMENT_START_COLS].values, outer_value=False)
        mask2 = mask.lookup(all_pts[SEGMENT_END_COLS].values, outer_value=False)
        filtered = all_pts[mask1 & mask2]

        if filtered.empty:
            L.warning("No axon segments found inside region of interest for GID %d", gid)
            return np.nan

        # total length for those filtered segments
        axon_length = _segment_lengths(filtered).sum()

        # Find axon segments with synapses; count synapses per each such segment.
        INDEX_COLS = [PRE_SECTION_ID, PRE_SEGMENT_ID]
        syn_per_segment = (
            edge_population.efferent_edges(gid, properties=INDEX_COLS).groupby(INDEX_COLS).size()
        )

        # The section ids of the MultiIndex in the DataFrame returned by ``_segment_points``
        # are returned in the same order they are read from file, but skipping the soma
        # because MorphIO never considers the soma as a section.
        #
        # For this reason, assuming that the soma has section id 0 in the file,
        # the resulting section ids of all the other sections is 1 less than the ones in the file.
        #
        # As a consequence, the section ids of the filtered points need to be incremented
        # to be consistent with the values returned by ``edge_population.efferent_edges``,
        # that are loaded using libsonata.
        df = filtered.index.to_frame(index=False)
        df[SECTION_ID] += 1
        index = pd.MultiIndex.from_frame(df)

        # count synapses on filtered segments
        synapse_count = syn_per_segment.loc[syn_per_segment.index.intersection(index)].sum()

    return (1.0 * synapse_count / synapses_per_bouton) / axon_length


def bouton_density(population, gid, synapses_per_bouton=1.0, mask=None):
    """Calculate bouton density for a given `gid`."""
    mask = _load_mask(mask)
    return _calc_bouton_density(population, gid, synapses_per_bouton, mask)


def sample_bouton_density(population, n, group=None, synapses_per_bouton=1.0, mask=None, n_jobs=1):
    """Sample bouton density.

    Args:
        population: edge population instance
        n: sample size
        group: cell group
        synapses_per_bouton: assumed number of synapses per bouton
        mask (str): region of interest mask
        n_jobs (int): number of parallel jobs (1 for single process, -1 to use all the cpus)

    Returns:
        numpy array of length min(n, N) with bouton density per cell,
        where N is the total number cells in the specified cell group.
    """
    gids = population.source.ids(group)
    if len(gids) > n:
        gids = np.random.choice(gids, size=n, replace=False)
    elif len(gids) == 0:
        L.warning("No GID matching selection for group '%s'", group)
        return np.empty(0)
    if n_jobs == 1:
        return _sample_bouton_density_task(population, gids, synapses_per_bouton, mask)
    else:
        return _sample_bouton_density_parallel(
            population, gids, synapses_per_bouton, mask, n_jobs=n_jobs
        )


def _sample_bouton_density_task(population, gids, synapses_per_bouton=1.0, mask=None):
    """Sample bouton density task."""
    mask = _load_mask(mask)
    return np.array(
        [_calc_bouton_density(population, gid, synapses_per_bouton, mask) for gid in gids]
    )


def _sample_bouton_density_parallel(
    population, gids, synapses_per_bouton=1.0, mask=None, n_jobs=-1
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
            population,
            chunk,
            synapses_per_bouton=synapses_per_bouton,
            mask=mask,
            task_group="sample_bouton_density",
        )
        for chunk in np.array_split(gids, n_chunks)
    ]
    # base_seed is None because the RNG is not used in the subprocesses
    results = run_parallel(tasks, n_jobs, base_seed=None)
    return np.concatenate([result.value for result in results])


def sample_pathway_synapse_count(population, n, pre=None, post=None, unique_gids=False):
    """Sample synapse count for pathway connections.

    Args:
        population: edge population instance
        n: sample size
        pre: presynaptic cell group
        post: postsynaptic cell group
        unique_gids(bool): don't use one GID more than once

    Returns:
        numpy array of length min(n, N) with synapse number per connection,
        where N is the total number of connections satisfying the constraints.
    """
    it = population.iter_connections(
        pre, post, shuffle=True, unique_node_ids=unique_gids, return_edge_count=True
    )
    return np.array([p[2] for p in itertools.islice(it, n)])
