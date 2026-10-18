"""TC01_C3DC_StaticData: static text and links on the C3DC home / Resources / About pages.

Katalon: Test Cases/C3DC_TestCases/Studies/StaticData/TC01_C3DC_StaticData
Input:   InputFiles/C3DC/C3DC_StaticData.xlsx  (one sheet per page)

Katalon navigated to /resources and /about by URL because clicking the menu did not work in the
pipeline; the same is done here.
"""
import pytest


@pytest.mark.c3dc
@pytest.mark.static
def test_TC01_C3DC_StaticData(c3dc):
    c3dc.accept_banner()
    c3dc.verify_static_data("V_HomePage")

    c3dc.goto("resources")
    c3dc.verify_static_data("V_ResourcesPage")

    c3dc.goto("about")
    c3dc.verify_static_data("V_AboutAboutPage")

    c3dc.assert_no_failures()
