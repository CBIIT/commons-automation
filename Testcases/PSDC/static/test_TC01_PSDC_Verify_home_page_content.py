"""TC01_PSDC_Verify_home_page_content — Python regression case."""

import pytest


@pytest.mark.psdc
@pytest.mark.regression
@pytest.mark.static
def test_TC01_PSDC_Verify_home_page_content(psdc):
    psdc.accept_banner()
    psdc.verify_static_data('HomePage')
    psdc.assert_no_failures()
