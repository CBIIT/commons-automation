"""Runtime UI identity selection must not supply expected clinical values."""
from pathlib import Path

import pytest

from Commons.compare import compare_tables
from Commons.db_source import MemgraphSource, Neo4jSource
from Commons.query_reader import QueryFile

pytestmark = pytest.mark.unit


def query_file():
    return QueryFile(
        path=Path("case.xlsx"),
        queries_by_tab={
            "SurvivalTab": "MATCH (sv:survival) WHERE sv.survival_id IN $ui_survival_ids "
                           "RETURN sv.survival_id AS `Survival ID`, "
                           "sv.last_known_survival_status AS Status",
            "ParticipantsTab": "MATCH (p:participant) RETURN p.participant_id",
        },
    )


def test_ui_binding_refreshes_identities_only_and_leaves_other_tabs_unbound():
    query = query_file()
    query.bind_ui_rows("ParticipantsTab", ["Participant ID"], [["P1"]])
    assert query.parameters_by_tab == {}
    query.bind_ui_rows("SurvivalTab", ["Status", "Survival ID"], [["WRONG STATUS", "FU2"]])
    assert query.parameters_by_tab == {"SurvivalTab": {"ui_survival_ids": ["FU2"]}}
    query.bind_ui_rows("SurvivalTab", ["Survival ID"], [["FU1"], ["FU1"]])
    assert query.parameters_by_tab["SurvivalTab"]["ui_survival_ids"] == ["FU1", "FU1"]
    query.bind_ui_rows("SurvivalTab", ["Survival ID"], [])
    assert query.parameters_by_tab["SurvivalTab"] == {"ui_survival_ids": []}


@pytest.mark.parametrize("header, rows", [
    (["Participant ID"], [["P1"]]),
    (["Survival ID"], [[None]]),
    (["Survival ID"], [["  "]]),
    (["Survival ID"], [[]]),
])
def test_ui_binding_fails_closed_when_identity_cannot_be_read(header, rows):
    with pytest.raises(ValueError, match="Survival ID"):
        query_file().bind_ui_rows("SurvivalTab", header, rows)


@pytest.mark.parametrize("source_class", [MemgraphSource, Neo4jSource])
def test_bolt_uses_bound_ids_and_database_values(source_class):
    calls = []
    identity = "FU'1"

    class Session:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def run(self, cypher, **kwargs):
            calls.append((cypher, kwargs))
            return [{"Survival ID": identity, "Status": "Alive"}]

    class Driver:
        def session(self):
            return Session()

    source = source_class("bolt://example.invalid", "user", "unused", tab_row_limit=13)
    source._driver = Driver()
    query = query_file()
    ui_rows = [[identity, "WRONG STATUS"]]
    query.bind_ui_rows("SurvivalTab", ["Survival ID", "Status"], ui_rows)
    result = source.fetch_tab_table(query, "SurvivalTab")
    cypher, kwargs = calls[-1]
    assert identity not in cypher
    assert "$ui_survival_ids" in cypher
    assert cypher.endswith("LIMIT 13")
    assert kwargs == {"parameters": {"ui_survival_ids": [identity]}}
    assert result.rows == [[identity, "Alive"]]
    assert not compare_tables(ui_rows, result.rows).passed

    source.fetch_tab_table(query, "ParticipantsTab")
    assert calls[-1][1] == {}  # Existing queries keep the original driver call.
