import numpy as np
import numpy.testing as npt
import pandas as pd
from bluepy import Circuit
from bluepy.enums import Segment, Synapse
from mock import MagicMock, Mock, patch

import connectome_tools.stats as test_module


@patch("neurom.get")
def test_bouton_density_1(nm_get):
    circuit = MagicMock(Circuit)
    circuit.connectome.efferent_synapses.return_value = [(1, 0), (2, 0), (2, 1)]
    nm_get.return_value = [10.0]
    actual = test_module.bouton_density(circuit, 42, synapses_per_bouton=1.5)
    npt.assert_almost_equal(actual, 0.2)


def test_bouton_density_2():
    mock_mask = Mock()
    mock_mask.lookup.return_value = np.array([False])
    circuit = MagicMock(Circuit)
    circuit.atlas.load_data.return_value = mock_mask
    circuit.morph.segment_points.return_value = pd.DataFrame(
        data=[
            [0.0, 1.0, 1.0, 0.0, 2.0, 2.0],  # both endpoints out of ROI
        ],
        columns=[
            Segment.X1,
            Segment.Y1,
            Segment.Z1,
            Segment.X2,
            Segment.Y2,
            Segment.Z2,
        ],
    )
    actual = test_module.bouton_density(circuit, 42, mask="Foo")
    npt.assert_equal(actual, np.nan)


def test_bouton_density_3():
    def _mock_lookup(points, outer_value):
        return np.all(points > 0, axis=-1)

    mock_mask = Mock()
    mock_mask.lookup.side_effect = _mock_lookup
    circuit = MagicMock(Circuit)
    circuit.atlas.load_data.return_value = mock_mask
    circuit.morph.segment_points.return_value = pd.DataFrame(
        data=[
            [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],  # first endpoint out of ROI
            [1.0, 1.0, 1.0, 3.0, 3.0, 3.0],  # both endpoints within ROI
            [1.0, 1.0, 1.0, 4.0, 4.0, 4.0],  # both endpoints within ROI
            [1.0, 1.0, 1.0, 5.0, 5.0, 5.0],  # both endpoints within ROI
            [1.0, 1.0, 1.0, 0.0, 0.0, 0.0],  # second endpoint out of ROI
        ],
        columns=[
            Segment.X1,
            Segment.Y1,
            Segment.Z1,
            Segment.X2,
            Segment.Y2,
            Segment.Z2,
        ],
        index=pd.MultiIndex.from_tuples(
            [
                (11, 0),  # "outer" segment
                (11, 1),  # "inner" segment
                (11, 2),  # "inner" segment
                (12, 0),  # "inner" segment
                (12, 1),  # "outer" segment
            ]
        ),
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


@patch("neurom.get")
def test_bouton_density_4(nm_get):
    circuit = MagicMock(Circuit)
    projection = Mock()
    projection.efferent_synapses.return_value = [(2, 1), (3, 1), (4, 2), (5, 2), (6, 2), (7, 3)]
    circuit.projection.return_value = projection
    nm_get.return_value = [10.0]
    actual = test_module.bouton_density(
        circuit, 42, projection="test_projection", synapses_per_bouton=1.5
    )
    circuit.projection.assert_called_with("test_projection")
    npt.assert_almost_equal(actual, 0.4)


@patch(test_module.__name__ + "._calc_bouton_density", side_effect=[42.0, 43.0])
def test_sample_bouton_density_1(mock_get):
    circuit = MagicMock(Circuit)
    circuit.cells.ids.return_value = [1, 2, 3]
    npt.assert_equal(test_module.sample_bouton_density(circuit, n=2), [42.0, 43.0])


@patch(test_module.__name__ + "._calc_bouton_density", side_effect=[42.0, 43.0])
def test_sample_bouton_density_2(mock_get):
    circuit = MagicMock(Circuit)
    circuit.cells.ids.return_value = []
    npt.assert_equal(test_module.sample_bouton_density(circuit, n=2), [])


def test_sample_pathway_synapse_count_1():
    circuit = MagicMock(Circuit)
    circuit.connectome.iter_connections.return_value = [(0, 0, 42), (0, 0, 43), (0, 0, 44)]
    npt.assert_equal(test_module.sample_pathway_synapse_count(circuit, n=2), [42, 43])


def test_sample_pathway_synapse_count_2():
    circuit = MagicMock(Circuit)
    projection = Mock()
    projection.iter_connections.return_value = [(0, 0, 101), (0, 0, 77), (0, 0, 2)]
    circuit.projection.return_value = projection
    actual = test_module.sample_pathway_synapse_count(circuit, projection="test_projection", n=2)
    npt.assert_equal(actual, [101, 77])
    circuit.projection.assert_called_with("test_projection")
