"""Open the GC /#/studies catalog and compare listing rows to Memgraph.

This is not Data explore (those tests stay under Testcases/GC/studies/).
"""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC01_GC_StudyListing(gc):
    gc.load_query_file("TC01_GC_StudyListing.xlsx")
    gc.accept_banner()
    gc.open_studies_listing()
    gc.verify_studies_listing()
    gc.assert_no_failures()
