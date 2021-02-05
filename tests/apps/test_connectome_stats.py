from click.testing import CliRunner

from connectome_tools.apps import connectome_stats as test_module


def test_app_help():
    runner = CliRunner()
    result = runner.invoke(test_module.app, ["--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.startswith("Usage")
