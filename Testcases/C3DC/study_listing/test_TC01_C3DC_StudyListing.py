"""TC01_C3DC_StudyListing — Python regression case."""

import pytest


@pytest.mark.c3dc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_C3DC_StudyListing(c3dc):
    c3dc.load_query_file('TC01_C3DC_StudyListing.xlsx')
    c3dc.accept_banner()
    c3dc.open_studies_listing()
    c3dc.verify_studies_listing()
    c3dc.assert_no_failures()
