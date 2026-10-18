"""TC01_GC_StaticData: static text and links on the GC home / About pages.

Katalon: Test Cases/CDS_TestCases/Studies/StaticData/TC01_GC_StaticData
Input:   InputFiles/GC/CDS_StaticData.xlsx  (one sheet per page)
"""
import pytest


@pytest.mark.gc
@pytest.mark.static
def test_TC01_GC_StaticData(gc):
    gc.accept_banner()
    gc.verify_static_data("V_HomePage")

    gc.click("NavBar/About_DropDown")
    gc.click("NavBar/About_AboutCDS-Btn")
    gc.verify_static_data("V_AboutCDSPage")

    gc.click("NavBar/About_DropDown")
    gc.click("NavBar/About_DataModel-Btn")
    gc.verify_static_data("V_AboutDataModelPage")

    gc.assert_no_failures()
