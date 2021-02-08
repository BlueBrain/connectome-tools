import pytest
from mock import Mock, patch
from psutil import Process

import connectome_tools.utils as test_module

_this_process = Mock(
    Process,
    **{"as_dict.return_value": {"pid": 1, "name": "N1", "username": "U1", "cmdline": "CMD1"}}
)


@patch(test_module.__name__ + ".psutil.Process", return_value=_this_process)
def test_exit_if_not_alone_with_single_process(process):
    with patch(
        test_module.__name__ + ".psutil.process_iter",
        return_value=iter(
            [
                Mock(Process, info={"pid": 1, "name": "N1", "username": "U1", "cmdline": "CMD1"}),
                Mock(Process, info={"pid": 2, "name": "N1", "username": "U1", "cmdline": "CMD2"}),
            ]
        ),
    ):
        result = test_module.exit_if_not_alone()
        assert result is None


@patch(test_module.__name__ + ".psutil.Process", return_value=_this_process)
def test_exit_if_not_alone_with_multiple_processes(process):
    with patch(
        test_module.__name__ + ".psutil.process_iter",
        return_value=iter(
            [
                Mock(Process, info={"pid": 1, "name": "N1", "username": "U1", "cmdline": "CMD1"}),
                Mock(Process, info={"pid": 2, "name": "N1", "username": "U1", "cmdline": "CMD1"}),
            ]
        ),
    ):
        with pytest.raises(SystemExit) as exc_info:
            test_module.exit_if_not_alone()
        assert exc_info.value.args[0] == 1


def test_runalone():
    @test_module.runalone
    def f():
        return "DONE"

    with patch(test_module.__name__ + ".exit_if_not_alone") as mocked:
        result = f()
        assert result == "DONE"
        mocked.assert_called_once()
