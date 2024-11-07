import os

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from parameterized import param, parameterized
from utils import TEST_DATA_DIR

from connectome_tools.dataset import _remove_duplicates, read_bouton_density, read_nsyn


@parameterized.expand(
    [
        param(
            _="all_mtypes",
            mtypes=None,
            expected=pd.DataFrame(
                [
                    ["*", 42.0, np.nan, np.nan, np.nan],
                    ["L1_DAC", 10.0, 0.0, 1.0, np.nan],
                    ["L23_MC", 30.0, 0.0, 1.0, np.nan],
                    ["SO_OLM", 50.0, 0.0, 1.0, np.nan],
                ],
                columns=["mtype", "mean", "std", "size", "sample"],
            ),
        ),
        param(
            _="filter_mtypes",
            mtypes={"L1_DAC"},
            expected=pd.DataFrame(
                [["L1_DAC", 10.0, 0.0, 1.0, np.nan]],
                columns=["mtype", "mean", "std", "size", "sample"],
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
                    ["SLM_PPA", "SO_BP", np.nan, np.nan, np.nan, np.nan],
                    ["SLM_PPA", "SP_AA", 3.0, 1.63, 3.0, "1,3,5"],
                ],
                columns=["from", "to", "mean", "std", "size", "sample"],
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
            ),
        ),
    ]
)
def test_read_nsyn(_, mtypes, expected):
    filepath = os.path.join(TEST_DATA_DIR, "nsyn_per_connection.tsv")

    actual = read_nsyn(filepath, mtypes=mtypes)

    assert_frame_equal(actual.reset_index(drop=True), expected.reset_index(drop=True))


def test__remove_duplicates_without_duplicates():
    df = pd.DataFrame(
        [
            ["SLM_PPA", "SLM_PPA", 16.2, 8.77, 5.0, "1,16,16,20,28"],
            ["SLM_PPA", "SP_AA", 3.0, 1.63, 3.0, "1,3,5"],
        ],
        columns=["from", "to", "mean", "std", "size", "sample"],
    )

    actual = _remove_duplicates(df, keys=["from", "to"], filepath="dummy")

    assert_frame_equal(df, actual)


def test__remove_duplicates_with_duplicates_and_same_values():
    df = pd.DataFrame(
        [
            ["SLM_PPA", "SLM_PPA", 16.2, 8.77, 5.0, "1,16,16,20,28"],
            ["SLM_PPA", "SP_AA", 3.0, 1.63, 3.0, "1,3,5"],
            ["SLM_PPA", "SP_AA", 3.0, 1.63, 3.0, "1,3,5"],
        ],
        columns=["from", "to", "mean", "std", "size", "sample"],
    )
    expected = pd.DataFrame(
        [
            ["SLM_PPA", "SLM_PPA", 16.2, 8.77, 5.0, "1,16,16,20,28"],
            ["SLM_PPA", "SP_AA", 3.0, 1.63, 3.0, "1,3,5"],
        ],
        columns=["from", "to", "mean", "std", "size", "sample"],
    )

    actual = _remove_duplicates(df, keys=["from", "to"], filepath="dummy")

    assert_frame_equal(expected, actual)


def test__remove_duplicates_with_duplicates_and_different_values():
    df = pd.DataFrame(
        [
            ["SLM_PPA", "SLM_PPA", 16.2, 8.77, 5.0, "1,16,16,20,28"],
            ["SLM_PPA", "SP_AA", 3.0, 1.63, 3.0, "1,3,5"],
            ["SLM_PPA", "SP_AA", 6.0, 1.63, 3.0, "1,3,5"],
        ],
        columns=["from", "to", "mean", "std", "size", "sample"],
    )

    with pytest.raises(ValueError, match="Duplicate rows with different values"):
        _remove_duplicates(df, keys=["from", "to"], filepath="dummy")
