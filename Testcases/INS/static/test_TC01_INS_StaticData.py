"""Verify static page content on the home and about pages."""

import pytest


@pytest.mark.ins
@pytest.mark.static
def test_TC01_INS_StaticData(ins):
    ins.verify_static_data("V_HomePage")
    ins.click("Navbar/About-Btn")
    ins.click("Navbar/About-INS-Btn")
    ins.verify_static_data("V_AboutInsPage")
    ins.assert_no_failures()
