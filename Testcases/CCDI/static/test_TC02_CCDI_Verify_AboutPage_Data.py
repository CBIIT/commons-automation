"""TC02_CCDI_Verify_AboutPage_Data — Python regression case."""

import pytest


@pytest.mark.ccdi
@pytest.mark.regression
@pytest.mark.static
def test_TC02_CCDI_Verify_AboutPage_Data(ccdi):
    ccdi.accept_banner()
    ccdi.click('Navbar/About-Btn')
    ccdi.click('Navbar/About-AboutCCDI-Btn')
    ccdi.verify_about_page_data()
    ccdi.assert_no_failures()
