"""Reference datasets access."""

import logging

import numpy as np
import pandas as pd

L = logging.getLogger(__name__)


def _remove_duplicates(df, keys, filepath):
    """Remove the duplicates and raise an exception in case of different rows with the same key."""
    duplicated = df.duplicated()
    if np.any(duplicated):
        L.warning("Duplicate rows with same values found in %s:\n%s", filepath, df[duplicated])
        df = df[~duplicated]
    duplicated = df.duplicated(subset=keys)
    if np.any(duplicated):
        L.warning("Duplicate rows with different values found in %s:\n%s", filepath, df[duplicated])
        raise ValueError("Duplicate rows with different values")
    return df


def read_bouton_density(filepath, mtypes=None):
    """Read bouton density data from .tsv file."""
    result = pd.read_csv(filepath, sep=r"\s+")
    result = _remove_duplicates(result, keys=["mtype"], filepath=filepath)
    if mtypes is not None:
        mask = result["mtype"].isin(mtypes)
        if np.any(~mask):
            unused_mtypes = result[~mask]["mtype"]
            L.warning("Unused mtypes: %s", ",".join(unused_mtypes))
        result = result[mask]
    return pd.DataFrame(result)  # supressing pylint 'maybe-no-member' warning


def read_nsyn(filepath, mtypes=None):
    """Read nsyn data from .tsv file."""
    result = pd.read_csv(filepath, sep=r"\s+")
    result = _remove_duplicates(result, keys=["from", "to"], filepath=filepath)
    if mtypes is not None:
        mask1 = result["from"].isin(mtypes)
        mask2 = result["to"].isin(mtypes)
        mask = np.logical_and(mask1, mask2)  # pylint: disable=assignment-from-no-return
        if np.any(~mask):
            unused_mtypes = result[~mask1]["from"].tolist() + result[~mask2]["to"].tolist()
            L.warning("Unused mtypes: %s", ",".join(unused_mtypes))
        result = result[mask]
    return pd.DataFrame(result)  # supressing pylint 'maybe-no-member' warning
