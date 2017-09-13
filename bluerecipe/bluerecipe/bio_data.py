""" Reference datasets access. """

import numpy as np
import pandas as pd


def read_bouton_density(filepath, mtypes=None, logger=None):
    """ Read bouton density data from .txt file. """
    result = pd.read_csv(filepath, sep=r"\s+")
    if mtypes is not None:
        mask = result['mtype'].isin(mtypes)
        if np.any(~mask) and logger is not None:
            unused_mtypes = result[~mask]['mtype']
            logger.warning("Some mtypes are not used in the circuit: %s" % ",".join(unused_mtypes))
        result = result[mask]
    return result
