import numpy as np
import numpy.testing as npt
import pandas as pd
from bluepy import Circuit, Section, Segment, Synapse
from bluepy.connectome import Connectome
from mock import MagicMock, Mock, patch

import connectome_tools.stats as test_module


def _get_segment_points(data, index_tuples=None):
    return pd.DataFrame(
        data=data,
        columns=[
            Segment.X1,
            Segment.Y1,
            Segment.Z1,
            Segment.X2,
            Segment.Y2,
            Segment.Z2,
        ],
        index=pd.MultiIndex.from_tuples(
            index_tuples or [(0, i) for i in range(len(data))],
            names=[Section.ID, Segment.ID],
        ),
    )


@patch.object(test_module, "_segment_points")
def test_bouton_density_1_without_mask(mock_segment_points):
    circuit = MagicMock(Circuit)
    circuit.connectome.efferent_synapses.return_value = [1, 2, 3]  # List of synapse IDs
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
    actual = test_module.bouton_density(circuit, gid=42, synapses_per_bouton=1.5)

    assert circuit.connectome.efferent_synapses.call_count == 1
    assert mock_segment_points.call_count == 1
    npt.assert_almost_equal(actual, expected)


@patch.object(test_module, "_segment_points")
def test_bouton_density_2_with_empty_mask(mock_segment_points):
    mock_mask = Mock()
    mock_mask.lookup.return_value = np.array([False])
    circuit = MagicMock(Circuit)
    circuit.atlas.load_data.return_value = mock_mask
    mock_segment_points.return_value = _get_segment_points(
        data=[
            [0.0, 1.0, 1.0, 0.0, 2.0, 2.0],  # both endpoints out of ROI
        ]
    )
    actual = test_module.bouton_density(circuit, 42, mask="Foo")
    npt.assert_equal(actual, np.nan)


@patch.object(test_module, "_segment_points")
def test_bouton_density_3_with_mask(mock_segment_points):
    def _mock_lookup(points, outer_value):
        return np.all(points > 0, axis=-1)

    mock_mask = Mock()
    mock_mask.lookup.side_effect = _mock_lookup
    circuit = MagicMock(Circuit)
    circuit.atlas.load_data.return_value = mock_mask
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
    circuit.connectome.efferent_synapses.return_value = pd.DataFrame(
        data=[
            [11, 0],  # "outer" segment
            [11, 1],  # "inner" segment
            [12, 0],  # "inner" segment
            [11, 1],  # "inner" segment
            [11, 1],  # "inner" segment
        ],
        columns=[
            Synapse.PRE_SECTION_ID,
            Synapse.PRE_SEGMENT_ID,
        ],
    )
    expected = (3 + 1) / sum(  # three synapses on (11, 1); one synapse on (12, 0)
        [
            np.sqrt(12),  # length((11, 1))
            np.sqrt(27),  # length((11, 2))
            np.sqrt(48),  # length((12, 0))
        ]
    )
    actual = test_module.bouton_density(circuit, 42, mask="Foo")
    npt.assert_almost_equal(actual, expected)


@patch.object(test_module, "_segment_points")
def test_bouton_density_4_without_mask_with_projection(mock_segment_points):
    circuit = MagicMock(Circuit)
    projection = MagicMock(Connectome)
    projection.efferent_synapses.return_value = [1, 2, 3, 4, 5, 6]
    circuit.projection.return_value = projection
    mock_segment_points.return_value = _get_segment_points(
        data=[
            [1.0, 1.0, 1.0, 3.0, 3.0, 3.0],
            [1.0, 1.0, 1.0, 4.0, 4.0, 4.0],
            [1.0, 1.0, 1.0, 5.0, 5.0, 5.0],
            [1.0, 1.0, 1.0, 6.0, 7.0, 8.0],
        ],
    )
    expected = (
        6  # synapse_count
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
    actual = test_module.bouton_density(
        circuit, gid=42, projection="test_projection", synapses_per_bouton=1.5
    )
    circuit.projection.assert_called_with("test_projection")
    assert projection.efferent_synapses.call_count == 1
    assert mock_segment_points.call_count == 1
    npt.assert_almost_equal(actual, expected)


@patch(test_module.__name__ + "._calc_bouton_density", side_effect=[42.0, 43.0])
def test_sample_bouton_density_1(_):
    circuit = MagicMock(Circuit)
    circuit.cells.ids.return_value = [1, 2, 3]
    actual = test_module.sample_bouton_density(circuit, n=2)
    npt.assert_equal(actual, [42.0, 43.0])


@patch(test_module.__name__ + "._calc_bouton_density", side_effect=[42.0, 43.0])
def test_sample_bouton_density_2(_):
    circuit = MagicMock(Circuit)
    circuit.cells.ids.return_value = []
    actual = test_module.sample_bouton_density(circuit, n=2)
    npt.assert_equal(actual, [])


def test_sample_pathway_synapse_count_1():
    circuit = MagicMock(Circuit)
    circuit.connectome.iter_connections.return_value = [(0, 0, 42), (0, 0, 43), (0, 0, 44)]
    actual = test_module.sample_pathway_synapse_count(circuit, n=2)
    npt.assert_equal(actual, [42, 43])


def test_sample_pathway_synapse_count_2():
    circuit = MagicMock(Circuit)
    projection = Mock()
    projection.iter_connections.return_value = [(0, 0, 101), (0, 0, 77), (0, 0, 2)]
    circuit.projection.return_value = projection
    actual = test_module.sample_pathway_synapse_count(circuit, projection="test_projection", n=2)
    npt.assert_equal(actual, [101, 77])
    circuit.projection.assert_called_with("test_projection")
