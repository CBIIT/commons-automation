"""TC01_CCDI_Verify_HomePage_Data — Python regression case."""

import pytest


@pytest.mark.ccdi
@pytest.mark.regression
@pytest.mark.smoke
@pytest.mark.static
def test_TC01_CCDI_Verify_HomePage_Data(ccdi):
    ccdi.accept_banner()
    ccdi.click('Navbar/Home-Btn')
    ccdi.verify_home_page()
    ccdi.verify_home_controls()
    ccdi.assert_no_failures()
