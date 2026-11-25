"""TC03_CCDI_Verify_ResourcesPage_Data — Python regression case."""

import pytest


@pytest.mark.ccdi
@pytest.mark.regression
@pytest.mark.static
def test_TC03_CCDI_Verify_ResourcesPage_Data(ccdi):
    ccdi.accept_banner()
    ccdi.click('Navbar/Home-Btn')
    ccdi.click('Navbar/Resources-Btn')
    ccdi.verify_static_data('ResourcesPage')
    ccdi.assert_no_failures()
