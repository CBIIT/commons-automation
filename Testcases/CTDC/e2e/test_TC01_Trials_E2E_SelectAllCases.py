"""Trials E2E: select all cases and download manifest (not yet ported from Katalon)."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
@pytest.mark.skip(reason="E2E Trials workflow (Select_case_checkbox, manifest download) is not converted yet.")
def test_TC01_Trials_E2E_SelectAllCases(ctdc):
    pass
