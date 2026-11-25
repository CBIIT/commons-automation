"""TC01_C3DC_Verify_StudyDetails_Set-1 — Python regression case."""

import pytest


@pytest.mark.c3dc
def test_TC01_C3DC_Verify_StudyDetails_Set_1(c3dc):
    c3dc.load_query_file('C3DC_StudyDetails.xlsx')
    c3dc.accept_banner()
    c3dc.begin_study_details_report('StudyDetails_Target')
    c3dc.open_studies_listing()
    c3dc.open_study_details('phs000463')
    c3dc.verify_study_details('phs000463')
    c3dc.goto('studies')
    c3dc.open_study_details('phs000464')
    c3dc.verify_study_details('phs000464')
    c3dc.goto('studies')
    c3dc.open_study_details('phs000465')
    c3dc.verify_study_details('phs000465')
    c3dc.goto('studies')
    c3dc.open_study_details('phs000466')
    c3dc.verify_study_details('phs000466')
    c3dc.goto('studies')
    c3dc.open_study_details('phs000467')
    c3dc.verify_study_details('phs000467')
    c3dc.goto('studies')
    c3dc.open_study_details('phs000468')
    c3dc.verify_study_details('phs000468')
    c3dc.goto('studies')
    c3dc.open_study_details('phs000469')
    c3dc.verify_study_details('phs000469')
    c3dc.goto('studies')
    c3dc.open_study_details('phs000470')
    c3dc.verify_study_details('phs000470')
    c3dc.goto('studies')
    c3dc.open_study_details('phs000471')
    c3dc.verify_study_details('phs000471')
    c3dc.assert_no_failures()
