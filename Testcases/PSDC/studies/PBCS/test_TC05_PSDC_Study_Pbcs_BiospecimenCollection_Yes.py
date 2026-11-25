"""TC05_PSDC_Study_Pbcs_BiospecimenCollection-Yes — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
def test_TC05_PSDC_Study_Pbcs_BiospecimenCollection_Yes(psdc):
    psdc.load_query_file('TC05_PSDC_Study_Pbcs_BiospecimenCollection-Yes.xlsx')
    psdc.accept_banner()
    psdc.open_explore()
    psdc.select_study('PBCS')
    psdc.select_filter('Studies/BiospecimenCollection', 'Yes')
    psdc.read_statbar()
    psdc.verify_tab('Studies')
    psdc.assert_no_failures()
