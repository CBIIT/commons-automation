"""Verify static page content on the home page, resources, about, and other pages listed in the test."""

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
