"""Diagnosis page boundaries supply identities, never expected clinical values."""
from pathlib import Path

import pytest

from Commons.compare import compare_tables
from Commons.db_source import MemgraphSource
from Commons.query_reader import QueryFile

pytestmark = pytest.mark.unit


def query_file():
    return QueryFile(Path("diagnosis.xlsx"), queries_by_tab={
        "DiagnosisTab": "MATCH (d:diagnosis) WHERE d.diagnosis_id IN $ui_diagnosis_ids "
                        "RETURN d.diagnosis_id AS `Diagnosis ID`, d.diagnosis AS Diagnosis",
    })


def test_binding_uses_diagnosis_header_and_refreshes_only_identities():
    query = query_file()
    query.bind_ui_rows("DiagnosisTab", ["Diagnosis", "Diagnosis ID"], [["Wrong value", "DX2"]])
    assert query.parameters_by_tab == {"DiagnosisTab": {"ui_diagnosis_ids": ["DX2"]}}
    query.bind_ui_rows("DiagnosisTab", ["Diagnosis ID"], [["DX1"], ["DX1"]])
    assert query.parameters_by_tab["DiagnosisTab"] == {"ui_diagnosis_ids": ["DX1", "DX1"]}
    query.bind_ui_rows("DiagnosisTab", ["Diagnosis ID"], [])
    assert query.parameters_by_tab["DiagnosisTab"] == {"ui_diagnosis_ids": []}


@pytest.mark.parametrize("header,rows", [
    (["Participant ID"], [["P1"]]),
    (["Diagnosis ID"], [[None]]),
    (["Diagnosis ID"], [[" "]]),
    (["Diagnosis ID"], [[]]),
])
def test_missing_diagnosis_identity_fails_closed(header, rows):
    with pytest.raises(ValueError, match="Diagnosis ID"):
        query_file().bind_ui_rows("DiagnosisTab", header, rows)


def test_diagnosis_values_remain_independent_of_ui_and_ids_are_bound():
    calls = []

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def run(self, query, **kwargs):
            calls.append((query, kwargs))
            return [{"Diagnosis ID": "DX'1", "Diagnosis": "Database diagnosis"}]

    class Driver:
        def session(self):
            return Session()

    source = MemgraphSource("bolt://example.invalid", "user", "unused", tab_row_limit=13)
    source._driver = Driver()
    query = query_file()
    ui_rows = [["DX'1", "Wrong UI diagnosis"]]
    query.bind_ui_rows("DiagnosisTab", ["Diagnosis ID", "Diagnosis"], ui_rows)
    expected = source.fetch_tab_table(query, "DiagnosisTab")
    text, kwargs = calls[0]
    assert "DX'1" not in text
    assert kwargs == {"parameters": {"ui_diagnosis_ids": ["DX'1"]}}
    assert text.endswith("LIMIT 13")
    assert expected.rows == [["DX'1", "Database diagnosis"]]
    assert not compare_tables(ui_rows, expected.rows).passed
