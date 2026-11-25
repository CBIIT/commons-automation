"""TC12_ICDC_Verify_Cart_CGC_ExportEntry — Python regression case."""

import pytest


@pytest.mark.icdc
@pytest.mark.regression
def test_TC12_ICDC_Verify_Cart_CGC_ExportEntry(icdc):
    icdc.accept_banner()
    icdc.file_cart.open_explore_files()
    icdc.file_cart.select_files(3)
    icdc.file_cart.add_selected()
    icdc.file_cart.open()
    icdc.file_cart.verify('TC12_ICDC_Verify_Cart_CGC_ExportEntry')
    icdc.file_cart.verify_cgc_entry('cgc-accounts.sbgenomics.com')
    icdc.file_cart.verify('TC12_ICDC_Verify_Cart_CGC_ExportEntry')
    icdc.assert_no_failures()
