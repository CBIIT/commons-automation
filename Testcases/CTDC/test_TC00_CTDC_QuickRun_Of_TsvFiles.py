"""QuickRun over TSV inputs (Katalon TC00; no Groovy script in Commons_Automation)."""

import pytest


@pytest.mark.ctdc
@pytest.mark.quickrun
@pytest.mark.skip(reason="TC00 QuickRun has no Katalon script to convert; use individual filter tests.")
def test_TC00_CTDC_QuickRun_Of_TsvFiles(ctdc):
    pass
