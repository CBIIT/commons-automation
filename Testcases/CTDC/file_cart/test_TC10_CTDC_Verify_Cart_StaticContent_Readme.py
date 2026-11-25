"""TC10_CTDC_Verify_Cart_StaticContent_Readme — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC10_CTDC_Verify_Cart_StaticContent_Readme(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open()
    ctdc.file_cart.verify_static()
    ctdc.file_cart.verify_guide()
    ctdc.assert_no_failures()
