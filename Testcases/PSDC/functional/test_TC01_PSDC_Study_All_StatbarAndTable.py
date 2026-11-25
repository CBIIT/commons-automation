"""TC01_PSDC_Study_All_StatbarAndTable — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_PSDC_Study_All_StatbarAndTable(psdc):
    psdc.load_query_file('TC01_PSDC_Study_All_StatbarAndTable.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
