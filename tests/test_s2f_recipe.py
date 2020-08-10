import pytest

from apps.s2f_recipe import validate_params


@pytest.mark.parametrize(
    "pathways_dict, expected_is_valid, expected_missing, expected_dict",
    [
        (
            {
                "bouton_reduction_factor": 1.0,
                "mean_syns_connection": 1.0,
                "cv_syns_connection": 1.0,
            },
            True,
            None,
            None,
        ),
        (
            {"bouton_reduction_factor": 1.0, "p_A": 1.0, "pMu_A": 0.0},
            True,
            None,
            None,
        ),
        (
            {
                "bouton_reduction_factor": 1.0,
                "mean_syns_connection": 1.0,
                "cv_syns_connection": 1.0,
                "p_A": 1.0,
                "pMu_A": 0.0,
            },
            True,
            None,
            {"bouton_reduction_factor": 1.0, "p_A": 1.0, "pMu_A": 0.0},
        ),
        (
            {
                "bouton_reduction_factor": 1.0,
                "mean_syns_connection": 1.0,
                "cv_syns_connection": 1.0,
                "p_A": 1.0,
            },
            False,
            {"pMu_A"},
            None,
        ),
        ({}, False, {"bouton_reduction_factor"}, None),
        (
            {"bouton_reduction_factor": 1.0},
            False,
            {"mean_syns_connection", "cv_syns_connection"},
            None,
        ),
        (
            {"bouton_reduction_factor": 1.0, "mean_syns_connection": 1.0},
            False,
            {"cv_syns_connection"},
            None,
        ),
    ],
)
def test_validate_params(
    pathways_dict, expected_is_valid, expected_missing, expected_dict
):
    # if expected_dict is None, then we expect that pathways_dict will not be modified
    if expected_dict is None:
        expected_dict = pathways_dict.copy()

    is_valid, missing = validate_params(pathways_dict)

    assert is_valid == expected_is_valid
    assert missing == expected_missing
    assert pathways_dict == expected_dict
