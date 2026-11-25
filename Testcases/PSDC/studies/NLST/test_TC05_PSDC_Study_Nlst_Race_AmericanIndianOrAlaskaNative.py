"""TC05_PSDC_Study_Nlst_Race-AmericanIndianOrAlaskaNative — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC05_PSDC_Study_Nlst_Race_AmericanIndianOrAlaskaNative(psdc):
    psdc.load_query_file('TC05_PSDC_Study_Nlst_Race-AmericanIndianOrAlaskaNative.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('NLST')
    psdc.select_filter('Participants/Race', 'american indian or alaska native')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
