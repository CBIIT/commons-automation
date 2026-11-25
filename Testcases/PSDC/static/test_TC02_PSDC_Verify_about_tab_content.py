"""TC02_PSDC_Verify_about_tab_content — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
@pytest.mark.static
def test_TC02_PSDC_Verify_about_tab_content(psdc):
    psdc.accept_banner()
    psdc.click('NavBar/About-Tab')
    psdc.click('NavBar/AboutPage-Link')
    psdc.verify_static_data('AboutPage')
    psdc.click('NavBar/About-Tab')
    psdc.click('NavBar/AccessData-Link')
    psdc.verify_static_data('AccessDataPage')
    psdc.click('NavBar/About-Tab')
    psdc.click('NavBar/AnalyzeData-Link')
    psdc.verify_static_data('AnalyzeDataPage')
    psdc.click('NavBar/About-Tab')
    psdc.click('NavBar/Support-Link')
    psdc.verify_static_data('SupportPage')
    psdc.assert_no_failures()
