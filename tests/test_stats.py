import numpy as np
import numpy.testing as npt
import pandas as pd
from bluepysnap.edges import EdgePopulation
from mock import MagicMock, Mock, patch

import connectome_tools.stats as test_module


def _get_segment_points(data, index_tuples=None):
    return pd.DataFrame(
        data=data,
        columns=[*test_module.SEGMENT_START_COLS, *test_module.SEGMENT_END_COLS],
        index=pd.MultiIndex.from_tuples(
            index_tuples or [(0, i) for i in range(len(data))],
            names=[test_module.SECTION_ID, test_module.SEGMENT_ID],
        ),
    )


@patch.object(test_module, "_segment_points")
def test_bouton_density_1_without_mask(mock_segment_points):
    population = MagicMock(EdgePopulation)
    population.efferent_edges.return_value = [1, 2, 3]  # List of synapse IDs
    mock_segment_points.return_value = _get_segment_points(
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

    assert population.efferent_edges.call_count == 1
    assert mock_segment_points.call_count == 1
    npt.assert_almost_equal(actual, expected)


@patch.object(test_module, "Atlas")
@patch.object(test_module, "_segment_points")
def test_bouton_density_2_with_empty_mask(mock_segment_points, mock_atlas):
    mock_mask = Mock()
    mock_mask.lookup.return_value = np.array([False])
    mock_atlas.load_data.return_value = mock_mask
    mock_segment_points.return_value = _get_segment_points(
        data=[
            [0.0, 1.0, 1.0, 0.0, 2.0, 2.0],  # both endpoints out of ROI
        ]
    )
    population = MagicMock(EdgePopulation)
    actual = test_module.bouton_density(population, 42, mask="Foo", atlas_path="Foo")
    npt.assert_equal(actual, np.nan)


@patch.object(test_module, "Atlas")
@patch.object(test_module, "_segment_points")
def test_bouton_density_3_with_mask(mock_segment_points, mock_atlas):
    def _mock_lookup(points, outer_value):
        return np.all(points > 0, axis=-1)

    mock_mask = Mock()
    mock_mask.lookup.side_effect = _mock_lookup
    mock_atlas.open.return_value = Mock(load_data=Mock(return_value=mock_mask))
    mock_segment_points.return_value = _get_segment_points(
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
            test_module.PRE_SECTION_ID,
            test_module.PRE_SEGMENT_ID,
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
