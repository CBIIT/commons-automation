"""TC01_INS_StaticData — Python regression case."""

import pytest


@pytest.mark.ins
@pytest.mark.regression
@pytest.mark.static
def test_TC01_INS_StaticData(ins):
    ins.accept_banner()
    ins.verify_static_data('V_HomePage')
    ins.click('Navbar/About-Btn')
    ins.click('Navbar/About-INS-Btn')
    ins.verify_static_data('V_AboutInsPage')
    ins.assert_no_failures()
