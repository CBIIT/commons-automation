"""Table Katalon-style lines bypass pytest capture while read_table_data runs."""
from Commons import action_log


def test_table_live_print_bypasses_pytest_capture(capsys):
    capman = action_log._capture_manager()
    assert capman is not None
    with action_log.pytest_table_output_live():
        mc = capman._global_capturing
        assert mc is not None and mc._state == "suspended"
        action_log.table_live_print("TABLE_LIVE_UNIT_MARKER")
    assert "TABLE_LIVE_UNIT_MARKER" not in capsys.readouterr().out
