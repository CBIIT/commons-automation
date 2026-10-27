"""Verify static page content on CCDI Hub home, About, and Policies pages."""

import pytest


@pytest.mark.ccdi
@pytest.mark.static
def test_TC01_CCDI_StaticData(ccdi):
    ccdi.accept_banner()
    ccdi.verify_static_data("HomePage")

    ccdi.click("Navbar/About-Btn")
    ccdi.click("Navbar/About-AboutCCDI-Btn")
    ccdi.verify_static_data("AboutCCDIPage")

    ccdi.click("Navbar/About-Btn")
    ccdi.click("Navbar/About-CCDITerms-Btn")
    ccdi.verify_static_data("AboutPoliciesPage")

    ccdi.assert_no_failures()
