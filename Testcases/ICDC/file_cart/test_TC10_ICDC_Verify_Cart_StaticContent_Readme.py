"""TC10_ICDC_Verify_Cart_StaticContent_Readme — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC10_ICDC_Verify_Cart_StaticContent_Readme(icdc):
    icdc.accept_banner()
    icdc.file_cart.open()
    icdc.file_cart.verify_static()
    icdc.file_cart.verify_guide()
    icdc.assert_no_failures()
