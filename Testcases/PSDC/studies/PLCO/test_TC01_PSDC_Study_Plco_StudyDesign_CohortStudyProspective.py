"""TC01_PSDC_Study_Plco_StudyDesign-CohortStudyProspective — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
@pytest.mark.smoke
def test_TC01_PSDC_Study_Plco_StudyDesign_CohortStudyProspective(psdc):
    psdc.load_query_file('TC01_PSDC_Study_Plco_StudyDesign-CohortStudyProspective.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PLCO')
    psdc.select_filter('Studies/StudyDesign', 'Cohort Study - Prospective')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
