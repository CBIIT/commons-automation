"""TC01_GC_StaticData — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
@pytest.mark.static
def test_TC01_GC_StaticData(gc):
    gc.accept_banner()
    gc.verify_static_data('HomePage')
    gc.click('NavBar/About_DropDown')
    gc.click('NavBar/About_AboutCDS-Btn')
    gc.verify_static_data('AboutCDSPage')
    gc.click('NavBar/About_DropDown')
    gc.click('NavBar/About_DataModel-Btn')
    gc.assert_no_failures()
