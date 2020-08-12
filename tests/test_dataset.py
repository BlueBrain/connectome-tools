import os

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal
from parameterized import param, parameterized

from connectome_tools.dataset import read_bouton_density, read_nsyn

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@parameterized.expand(
    [
        param(
            _="all_mtypes",
            mtypes=None,
            expected=pd.DataFrame(
                [
                    ["*", 42.0, None, None, None],
                    ["L1_DAC", 10.0, 0.0, 1.0, None],
                    ["L23_MC", 30.0, 0.0, 1.0, None],
                    ["SO_OLM", 50.0, 0.0, 1.0, None],
                ],
                columns=["mtype", "mean", "std", "size", "sample"],
                dtype=np.float64,
            ),
        ),
        param(
            _="filter_mtypes",
            mtypes={"L1_DAC"},
            expected=pd.DataFrame(
                [["L1_DAC", 10.0, 0.0, 1.0, None]],
                columns=["mtype", "mean", "std", "size", "sample"],
                dtype=np.float64,
            ),
        ),
    ]
)
def test_read_bouton_density(_, mtypes, expected):
    filepath = os.path.join(TEST_DATA_DIR, "bouton_density.tsv")

    actual = read_bouton_density(filepath, mtypes=mtypes)

    assert_frame_equal(actual.reset_index(drop=True), expected.reset_index(drop=True))


@parameterized.expand(
    [
        param(
            _="all_mtypes",
            mtypes=None,
            expected=pd.DataFrame(
                [
                    ["SLM_PPA", "SLM_PPA", 16.2, 8.77, 5.0, "1,16,16,20,28"],
                    ["SLM_PPA", "SO_BP", None, None, None, None],
                    ["SLM_PPA", "SP_AA", 3.0, 1.63, 3.0, "1,3,5"],
                ],
                columns=["from", "to", "mean", "std", "size", "sample"],
                dtype=np.float64,
            ),
        ),
        param(
            _="filter_mtypes",
            mtypes={"SLM_PPA", "SP_AA"},
            expected=pd.DataFrame(
                [
                    ["SLM_PPA", "SLM_PPA", 16.2, 8.77, 5.0, "1,16,16,20,28"],
                    ["SLM_PPA", "SP_AA", 3.0, 1.63, 3.0, "1,3,5"],
                ],
                columns=["from", "to", "mean", "std", "size", "sample"],
                dtype=np.float64,
            ),
        ),
    ]
)
def test_read_nsyn(_, mtypes, expected):
    filepath = os.path.join(TEST_DATA_DIR, "nsyn_per_connection.tsv")

    actual = read_nsyn(filepath, mtypes=mtypes)

    assert_frame_equal(actual.reset_index(drop=True), expected.reset_index(drop=True))
