"""TC10_GC_Verify_Cart_StaticContent_Readme — Python regression case."""

import pytest


@pytest.mark.gc
@pytest.mark.regression
def test_TC10_GC_Verify_Cart_StaticContent_Readme(gc):
    gc.accept_banner()
    gc.file_cart.open()
    gc.file_cart.verify_static()
    gc.file_cart.verify_guide()
    gc.assert_no_failures()
