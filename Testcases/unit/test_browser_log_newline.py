"""Live [Browser] lines start on a new row after pytest's test name."""
from Commons import action_log


def test_live_console_line_prefix_once_per_test():
    action_log.prepare_test_live_console()
    assert action_log._live_console_line("[Browser] first") == "\n[Browser] first"
    assert action_log._live_console_line("[Browser] second") == "[Browser] second"
