"""Verify static page content on CTDC home, Data, Resources, About, and Request Access pages."""

import pytest


@pytest.mark.ctdc
@pytest.mark.static
def test_TC01_CTDC_StaticData(ctdc):
    ctdc.accept_banner()
    ctdc.verify_static_data("HomePage")

    ctdc.click("NavBar/Data-Tab")
    ctdc.click("NavBar/Data-Cloud-Btn")
    ctdc.verify_static_data("DataCloudPage")

    ctdc.click("NavBar/Data-Tab")
    ctdc.click("NavBar/Data-Harmonization-Btn")
    ctdc.verify_static_data("DataHarmonizationPage")

    ctdc.click("NavBar/Data-Tab")
    ctdc.click("NavBar/Data-Terms-Btn")
    ctdc.verify_static_data("DataTermsPage")

    ctdc.click("NavBar/Data-Tab")
    ctdc.click("NavBar/Data-Submission-Btn")
    ctdc.verify_static_data("DataSubmissionPage")

    ctdc.click("NavBar/Resources-Tab")
    ctdc.click("NavBar/Resources-GraphQL-Btn")
    ctdc.verify_static_data("ResourcesGraphQLPage")

    ctdc.click("NavBar/Resources-Tab")
    ctdc.click("NavBar/Resources-AddtlInfo-Btn")
    ctdc.verify_static_data("ResourcesInfoPage")

    ctdc.click("NavBar/About-Tab")
    ctdc.click("NavBar/About-Purpose-Btn")
    ctdc.verify_static_data("AboutPurposePage")

    ctdc.click("NavBar/About-Tab")
    ctdc.click("NavBar/About-ContactUs-Btn")
    ctdc.verify_static_data("AboutContactPage")

    ctdc.click("NavBar/RequestAccess-Btn")
    ctdc.click("RequestAccess_page/ObtainCommonsDropdown")
    ctdc.click("RequestAccess_page/ObtainDbgapDropdown")
    ctdc.click("RequestAccess_page/RequestAccessDropdown")
    ctdc.click("RequestAccess_page/AccessDatasetsDropdown")
    ctdc.verify_static_data("RequestAccessPage")

    ctdc.assert_no_failures()
