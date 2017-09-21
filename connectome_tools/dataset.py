""" Reference datasets access. """

import logging

import numpy as np
import pandas as pd


L = logging.getLogger(__name__)


def read_bouton_density(filepath, mtypes=None):
    """ Read bouton density data from .tsv file. """
    result = pd.read_csv(filepath, sep="\t")
    if mtypes is not None:
        mask = result['mtype'].isin(mtypes)
        if np.any(~mask):
            unused_mtypes = result[~mask]['mtype']
            L.warn("Unused mtypes: %s", ",".join(unused_mtypes))
        result = result[mask]
    return pd.DataFrame(result)  # supressing pylint 'maybe-no-member' warning


def read_nsyn(filepath, mtypes=None):
    """ Read nsyn data from .tsv file. """
    result = pd.read_csv(filepath, sep="\t")
    if mtypes is not None:
        mask1 = result['from'].isin(mtypes)
        mask2 = result['to'].isin(mtypes)
        mask = np.logical_and(mask1, mask2)
        if np.any(~mask):
            unused_mtypes = result[~mask1]['from'].tolist() + result[~mask2]['to'].tolist()
            L.warn("Unused mtypes: %s", ",".join(unused_mtypes))
        result = result[mask]
    return pd.DataFrame(result)  # supressing pylint 'maybe-no-member' warning
