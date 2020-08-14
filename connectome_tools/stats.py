""" Calculating connectome stats. """

import itertools
import logging

import neurom as nm
import numpy as np
from bluepy.v2 import Segment, Synapse
from voxcell import ROIMask

L = logging.getLogger(__name__)


def _segment_lengths(segments):
    """ Find segment lengths given a DataFrame returned by morph.spatial_index() query. """
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


def _calc_bouton_density(circuit, gid, synapses_per_bouton, mask):
    """ Calculate bouton density for a given `gid`. """
    if mask is None:
        # count all efferent synapses and total axon length
        synapse_count = len(circuit.connectome.efferent_synapses(gid))
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
        INDEX_COLS = [Synapse.PRE_SECTION_ID, "_PRE_SEGMENT_ID"]
        syn_per_segment = (
            circuit.connectome.efferent_synapses(gid, properties=INDEX_COLS)
            .groupby(INDEX_COLS)
            .size()
        )

        # count synapses on filtered segments
        synapse_count = syn_per_segment.loc[
            syn_per_segment.index.intersection(filtered.index)
        ].sum()

    return (1.0 * synapse_count / synapses_per_bouton) / axon_length


def bouton_density(circuit, gid, synapses_per_bouton=1.0, mask=None):
    """ Calculate bouton density for a given `gid`. """
    mask = _load_mask(circuit, mask)
    return _calc_bouton_density(circuit, gid, synapses_per_bouton, mask)


def sample_bouton_density(circuit, n, group=None, synapses_per_bouton=1.0, mask=None):
    """
    Sample bouton density.

    Args:
        n: sample size
        group: cell group
        synapses_per_bouton: assumed number of synapses per bouton

    Returns:
        numpy array of length min(n, N) with bouton density per cell,
        where N is the total number cells in the specified cell group.
    """
    gids = circuit.cells.ids(group)
    if len(gids) > n:
        gids = np.random.choice(gids, size=n, replace=False)
    elif len(gids) == 0:
        L.warning("No GID matching selection for group '%s'", group)
    mask = _load_mask(circuit, mask)
    return np.array([_calc_bouton_density(circuit, gid, synapses_per_bouton, mask) for gid in gids])


def sample_pathway_synapse_count(circuit, n, pre=None, post=None, unique_gids=False):
    """
    Sample synapse count for pathway connections.

    Args:
        n: sample size
        pre: presynaptic cell group
        post: postsynaptic cell group
        unique_gids(bool): don't use one GID more than once

    Returns:
        numpy array of length min(n, N) with synapse number per connection,
        where N is the total number of connections satisfying the constraints.
    """
    it = circuit.connectome.iter_connections(
        pre, post, shuffle=True, unique_gids=unique_gids, return_synapse_count=True
    )
    return np.array([p[2] for p in itertools.islice(it, n)])
