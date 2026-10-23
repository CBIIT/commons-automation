"""Open the C3DC /studies catalog and compare listing rows to Memgraph.

This is not Explore Participants → Studies (those tests stay under Testcases/C3DC/studies/).
"""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
def test_TC01_C3DC_StudyListing(c3dc):
    c3dc.load_query_file("TC01_C3DC_StudyListing.xlsx")
    c3dc.accept_banner()
    c3dc.open_studies_listing()
    c3dc.verify_studies_listing()
    c3dc.assert_no_failures()
