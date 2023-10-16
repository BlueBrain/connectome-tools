import numpy as np
import numpy.testing as npt
import pandas as pd
import pytest
from bluepysnap.edges import EdgePopulation
from mock import MagicMock, Mock, patch
from voxcell import ROIMask

import connectome_tools.stats as test_module
from connectome_tools.utils import Properties


def _get_axon_points(data, index_tuples=None):
    return pd.DataFrame(
        data=data,
        columns=[*test_module.SEGMENT_START_COLS, *test_module.SEGMENT_END_COLS],
        index=pd.MultiIndex.from_tuples(
            index_tuples or [(0, i) for i in range(len(data))],
            names=[Properties.SECTION_ID, Properties.SEGMENT_ID],
        ),
    )


def test__axon_points():
    rng = np.random.default_rng(42)

    def _section(id_, type_):
        pts = np.round(rng.random((4, 3)) * 100, 1)
        return Mock(points=pts, type=type_, id=id_)

    types = rng.integers(1, 5, 10)
    sections = [_section(i, t) for i, t in enumerate(types)]
    mock_morph = Mock(iter=Mock(return_value=sections))
    res = test_module._axon_points(mock_morph)

    seg_id = np.where(types == 2)[0] + 1  # +1 for the soma-shift (soma = 0)
    idx = [(i, j) for i in seg_id for j in range(3)]

    expected = pd.DataFrame(
        {
            "x1": [83.3, 83.2, 28.8, 66.5, 45.9, 11.5],
            "y1": [70.0, 80.5, 68.2, 70.5, 56.9, 66.8],
            "z1": [31.2, 38.7, 14.0, 78.1, 14.0, 47.1],
            "x2": [83.2, 28.8, 20.0, 45.9, 11.5, 56.5],
            "y2": [80.5, 68.2, 0.7, 56.9, 66.8, 76.5],
            "z2": [38.7, 14.0, 78.7, 14.0, 47.1, 63.5],
        },
        index=pd.MultiIndex.from_tuples(idx, names=["section_id", "segment_id"]),
    )
    assert res.equals(expected)


@patch.object(test_module.Atlas, "open")
def test__load_mask(mock_atlas_open):
    mock_atlas_open.return_value = mock_atlas = Mock(load_data=Mock())
    assert test_module._load_mask(None, "Bar") is None
    mock_atlas_open.assert_not_called()

    assert test_module._load_mask("Foo", "Bar") is not None
    mock_atlas_open.assert_called_once_with("Bar")
    mock_atlas.load_data.assert_called_once_with("Foo", cls=ROIMask)

    with pytest.raises(ValueError, match="Missing atlas path"):
        test_module._load_mask("Foo", None)


@patch.object(test_module, "_axon_points")
def test_bouton_density_1_without_mask(mock_axon_points):
    population = MagicMock(EdgePopulation)
    population.iter_connections.return_value = [[None, None, 3]]  # number of connections
    mock_axon_points.return_value = _get_axon_points(
        data=[
            [1.0, 1.0, 1.0, 3.0, 3.0, 3.0],
            [1.0, 1.0, 1.0, 4.0, 4.0, 4.0],
            [1.0, 1.0, 1.0, 5.0, 5.0, 5.0],
            [1.0, 1.0, 1.0, 6.0, 7.0, 8.0],
        ],
    )
    expected = (
        3  # synapse_count
        / 1.5  # synapses_per_bouton
        / sum(  # axon_length
            [
                np.sqrt(4 + 4 + 4),
                np.sqrt(9 + 9 + 9),
                np.sqrt(16 + 16 + 16),
                np.sqrt(25 + 36 + 49),
            ]
        )
    )
    actual = test_module.bouton_density(population, gid=42, synapses_per_bouton=1.5)

    assert population.iter_connections.call_count == 1
    assert mock_axon_points.call_count == 1
    npt.assert_almost_equal(actual, expected)


@patch.object(test_module, "Atlas")
@patch.object(test_module, "_axon_points")
def test_bouton_density_2_with_empty_mask(mock_axon_points, mock_atlas):
    mock_mask = Mock()
    mock_mask.lookup.return_value = np.array([False])
    mock_atlas.load_data.return_value = mock_mask
    mock_axon_points.return_value = _get_axon_points(
        data=[
            [0.0, 1.0, 1.0, 0.0, 2.0, 2.0],  # both endpoints out of ROI
        ]
    )
    population = MagicMock(EdgePopulation)
    actual = test_module.bouton_density(population, 42, mask="Foo", atlas_path="Foo")
    npt.assert_equal(actual, np.nan)


@patch.object(test_module, "Atlas")
@patch.object(test_module, "_axon_points")
def test_bouton_density_3_with_mask(mock_axon_points, mock_atlas):
    def _mock_lookup(points, outer_value):
        return np.all(points > 0, axis=-1)

    mock_mask = Mock()
    mock_mask.lookup.side_effect = _mock_lookup
    mock_atlas.open.return_value = Mock(load_data=Mock(return_value=mock_mask))
    mock_axon_points.return_value = _get_axon_points(
        data=[
            [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],  # first endpoint out of ROI
            [1.0, 1.0, 1.0, 3.0, 3.0, 3.0],  # both endpoints within ROI
            [1.0, 1.0, 1.0, 4.0, 4.0, 4.0],  # both endpoints within ROI
            [1.0, 1.0, 1.0, 5.0, 5.0, 5.0],  # both endpoints within ROI
            [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],  # second endpoint out of ROI
        ],
        # the section id is decremented by 1 to be consistent with bluepy 2.3.0
        index_tuples=[
            (11 - 1, 0),  # "outer" segment
            (11 - 1, 1),  # "inner" segment
            (11 - 1, 2),  # "inner" segment
            (12 - 1, 0),  # "inner" segment
            (12 - 1, 1),  # "outer" segment
        ],
    )
    population = MagicMock(EdgePopulation)
    population.efferent_edges.return_value = pd.DataFrame(
        data=[
            [11, 0],  # "outer" segment
            [11, 1],  # "inner" segment
            [12, 0],  # "inner" segment
            [11, 1],  # "inner" segment
            [11, 1],  # "inner" segment
        ],
        columns=[
            Properties.PRE_SECTION_ID,
            Properties.PRE_SEGMENT_ID,
        ],
    )
    expected = (3 + 1) / sum(  # three synapses on (11, 1); one synapse on (12, 0)
        [
            np.sqrt(12),  # length((11, 1))
            np.sqrt(27),  # length((11, 2))
            np.sqrt(48),  # length((12, 0))
        ]
    )
    actual = test_module.bouton_density(population, 42, mask="Foo", atlas_path="Foo")
    npt.assert_almost_equal(actual, expected)


@patch(test_module.__name__ + "._calc_bouton_density", side_effect=[42.0, 43.0])
def test_sample_bouton_density_1(_):
    population = MagicMock(EdgePopulation)
    population.source.ids.return_value = [1, 2, 3]  # List of synapse IDs
    actual = test_module.sample_bouton_density(population, n=2)
    npt.assert_equal(actual, [42.0, 43.0])


@patch(test_module.__name__ + "._calc_bouton_density", side_effect=[42.0, 43.0])
def test_sample_bouton_density_2(_):
    population = MagicMock(EdgePopulation)
    population.source.ids.return_value = []  # List of synapse IDs
    actual = test_module.sample_bouton_density(population, n=2)
    npt.assert_equal(actual, [])


def test_sample_pathway_synapse_count_1():
    population = MagicMock(EdgePopulation)
    population.iter_connections.return_value = [(0, 0, 42), (0, 0, 43), (0, 0, 44)]
    actual = test_module.sample_pathway_synapse_count(population, n=2)
    npt.assert_equal(actual, [42, 43])
