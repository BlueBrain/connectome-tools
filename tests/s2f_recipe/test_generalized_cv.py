from bluepy.v2 import Circuit
from mock import MagicMock

import connectome_tools.s2f_recipe.generalized_cv as test_module


def test_execute():
    cv = 0.32
    expected = {("*", "*"): {"cv_syns_connection": cv}}
    circuit = MagicMock(Circuit)

    actual = test_module.execute(circuit, cv)

    assert actual == expected
