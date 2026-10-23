"""Verify static page content on the home and about pages."""

import pytest


@pytest.mark.c3dc
@pytest.mark.static
def test_TC01_C3DC_StaticData(c3dc):
    c3dc.accept_banner()
    c3dc.verify_static_data("HomePage")
    c3dc.goto("about")
    c3dc.verify_static_data("AboutPage")
    c3dc.assert_no_failures()
