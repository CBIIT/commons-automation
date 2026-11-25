"""C3DC participant cells follow displayed headers, including new clinical columns."""
from unittest.mock import Mock

import pytest

from Commons.table_reader import read_table_header_data, read_table_row_data

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("headers, cells", [
    (["", "Participant ID", "Available CPI Mapping", "Sex at Birth", "Diagnosis",
      "Diagnosis Category", "Age at Diagnosis (days)", "Anatomic Site",
      "Last Known Survival Status", "Age at Last Known Survival Status",
      "Treatment Type", "Age at Treatment Start"],
     ["", "P1", "2\n1", "Female", "Diagnosis A; Diagnosis B", "Category",
      "100; 200", "blood", "Alive", "300", "Radiation", "250"]),
    # Optional columns can be toggled or reordered without shifting the cell/header mapping.
    (["", "Participant ID", "Race", "Age at Treatment Start", "Available CPI Mapping"],
     ["", "P1", "White", "Not Reported", "2"]),
])
def test_participant_reader_keeps_every_displayed_data_column(headers, cells):
    ui = Mock()
    body = "//*[@id='participant_tab_table']//tbody"
    ui.text.side_effect = lambda xpath: cells[int(xpath.rsplit("[", 1)[1][:-1]) - 1]
    indices = [i for i, name in enumerate(headers) if i > 0 and name != "Available CPI Mapping"]

    assert read_table_header_data("C3DC", "//*[@id='participant_tab_table']", headers) == [headers[i] for i in indices]
    assert read_table_row_data(
        "C3DC", ui, tbl_main="//*[@id='participant_tab_table']", tbl_bdy=body,
        row_index=1, col_header=headers, trace=False,
    ) == [cells[i] for i in indices]
    assert [call.args[0] for call in ui.text.call_args_list] == [
        f"{body}/tr[1]/td[{i + 1}]" for i in indices
    ]
