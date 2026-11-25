"""TC12_CTDC_Verify_Cart_CGC_ExportEntry — Python regression case."""

import pytest


@pytest.mark.ctdc
@pytest.mark.regression
def test_TC12_CTDC_Verify_Cart_CGC_ExportEntry(ctdc):
    ctdc.accept_banner()
    ctdc.file_cart.open_explore_files()
    ctdc.file_cart.select_files(3)
    ctdc.file_cart.add_selected()
    ctdc.file_cart.open()
    ctdc.file_cart.verify('TC12_CTDC_Verify_Cart_CGC_ExportEntry')
    ctdc.file_cart.verify_cgc_entry('cgc-accounts.sbgenomics.com')
    ctdc.file_cart.verify('TC12_CTDC_Verify_Cart_CGC_ExportEntry')
    ctdc.assert_no_failures()
