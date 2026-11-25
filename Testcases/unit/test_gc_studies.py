"""GC listing representatives must match a complete independent source row."""
import json
import pytest
from Commons.apps.gc.studies import _resolve_source_study_rows
from Commons.compare import compare_tables
from Commons.db_source import Table

pytestmark = pytest.mark.unit
HEADER = ['Study Accession','Study Version','Study Name','Program Name','Data Types','Study Access','Number of Participants','Number of Files']
SOURCE = [
    ['accession','v1','Study A','Program A','Genomics','Open','10','1000'],
    ['accession','v2','Study B','Program B','Imaging','Controlled','20','2000'],
]


@pytest.mark.parametrize('problem', [None,'name','program','counts','mixed_source','accession'])
def test_accession_representative_requires_all_fields_from_one_source(problem):
    actual = SOURCE[1][:]
    actual[7] = '2,000'
    if problem == 'name': actual[2] = 'Unknown study'
    if problem == 'program': actual[3] = 'Wrong program'
    if problem == 'counts': actual[7] = '1,999'
    if problem == 'mixed_source': actual[3] = SOURCE[0][3]
    if problem == 'accession': actual[0] = 'another-accession'
    default = SOURCE[0][:]
    default[2] = json.dumps({'source_rows': SOURCE})
    ui, db = Table(HEADER[:],[actual]), Table(HEADER[:],[default])

    _resolve_source_study_rows(ui,db)

    assert compare_tables(ui.rows,db.rows,ui.header,db.header).passed == (problem is None)


def test_single_source_listing_rows_are_not_changed():
    ui,db = Table(HEADER[:],[SOURCE[0][:]]),Table(HEADER[:],[SOURCE[0][:]])
    _resolve_source_study_rows(ui,db)
    assert db.rows == [SOURCE[0]]
