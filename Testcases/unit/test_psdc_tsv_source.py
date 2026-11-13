"""PSDC release merging and SQL integration without a browser or live data."""
from pathlib import Path

import pytest

from Commons.apps.psdc.tsv_source import PsdcTsvSource, load_psdc_merged_frames, psdc_node_for_filename
from Commons.query_reader import QueryFile
from Commons.tsv_source import TsvSource

pytestmark = pytest.mark.unit


def _release(root, study, date, participants):
    folder = root / study / date
    folder.mkdir(parents=True)
    (folder / "study.tsv.txt").write_text(f"study_short_name\tstudy_name\n{study}\tStudy {study}\n")
    (folder / "participant.tsv").write_text("participant_id\trace\n" + participants)
    return folder


def test_merge_keeps_study_scoped_ids_and_latest_release(tmp_path):
    _release(tmp_path, "NLST", "2026-01-01", "001\tUnknown\n002\tWhite\n")
    _release(tmp_path, "NLST", "2026-02-01", "001\tAsian\n")
    _release(tmp_path, "PBCS", "2026-01-01", "001\tWhite\n")
    frame = load_psdc_merged_frames(tmp_path)["participant"]
    actual = frame.set_index(["study.study_short_name", "participant_id"])["race"].to_dict()
    assert actual == {("NLST", "001"): "Asian", ("NLST", "002"): "White", ("PBCS", "001"): "White"}


def test_overlapping_release_files_are_rejected(tmp_path):
    folder = _release(tmp_path, "NLST", "2026-01-01", "001\tWhite\n")
    (folder / "old_participant.txt").write_text("participant_id\trace\n001\tAsian\n")
    with pytest.raises(ValueError, match="Overlapping PSDC participant"):
        load_psdc_merged_frames(tmp_path)


def test_missing_key_and_archives_only_have_clear_errors(tmp_path):
    with pytest.raises(RuntimeError, match="No dated PSDC releases"):
        load_psdc_merged_frames(tmp_path)
    folder = _release(tmp_path, "NLST", "2026-01-01", "001\tWhite\n")
    (folder / "participant.tsv").write_text("wrong_id\trace\n001\tWhite\n")
    with pytest.raises(ValueError, match="missing key column 'participant_id'"):
        load_psdc_merged_frames(tmp_path)


def test_excel_sql_and_factory_use_psdc_source(tmp_path):
    _release(tmp_path, "NLST", "2026-01-01", "001\tWhite\n002\tAsian\n")
    source = TsvSource(app="PSDC", tsv_root=str(tmp_path), tab_row_limit=1)
    assert isinstance(source, PsdcTsvSource)
    try:
        query = QueryFile(path=Path("TC01_PSDC.xlsx"))
        query.stat_bar_query = 'SELECT COUNT(*) AS "Participants" FROM df_participant'
        query.queries_by_tab["StudiesTab"] = "SELECT participant_id FROM df_participant ORDER BY participant_id"
        assert source.fetch_stat_bar_table(query).rows == [["2"]]
        assert source.fetch_tab_table(query, "StudiesTab").rows == [["001"]]
        assert source.fetch_tab_table(query, "StudiesTab", apply_row_limit=False).rows == [["001"], ["002"]]
    finally:
        source.close()


@pytest.mark.parametrize("name,node", [
    ("PBCS_Data_Loading_Template - study.tsv.txt", "study"),
    ("PLCO_Data_Loading_Template - study_country.tsv", "study_country"),
    ("NLST_File_Transfer_Manifest - study files.tsv", "file"),
    ("PLCO_participant_data_final.txt", "participant"),
])
def test_loading_template_names(name, node):
    assert psdc_node_for_filename(name) == node
