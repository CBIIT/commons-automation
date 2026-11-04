"""Regressions for a filtered stat bar paired with a stale participant grid."""
import pytest

from Commons.apps.c3dc import C3DC

pytestmark = pytest.mark.unit


def snapshot(*sexes):
    return {
        "headers": ["", "Participant ID", "Study ID", "Sex at Birth", "Race"],
        "rows": [["", f"P{i}", "phs002431", sex, "White"] for i, sex in enumerate(sexes)],
    }


def test_male_filter_rejects_same_study_grid_with_female_rows():
    assert not C3DC._participant_snapshot_matches_filters(snapshot("Male", "Female"), "phs002431", {"Male"})
    assert C3DC._participant_snapshot_matches_filters(snapshot("Male", "Male"), "phs002431", {"Male"})


def test_study_and_selected_sex_must_both_match():
    assert not C3DC._participant_snapshot_matches_filters(snapshot("Male"), "phs000463", {"Male"})
    assert not C3DC._participant_snapshot_matches_filters(snapshot("Male"), "phs002431", {"Female"})


def test_multiple_checked_sexes_use_or_semantics_and_unfiltered_sex_is_allowed():
    mixed = snapshot("Male", "Female")
    assert C3DC._participant_snapshot_matches_filters(mixed, "phs002431", {"Male", "Female"})
    assert C3DC._participant_snapshot_matches_filters(mixed, "phs002431", set())


def test_column_position_is_derived_from_headers():
    data = {"headers": ["Sex at Birth", "Study ID"], "rows": [["Male", "phs002431"]]}
    assert C3DC._participant_snapshot_matches_filters(data, "phs002431", {"Male"})
    assert not C3DC._participant_snapshot_matches_filters({"headers": ["Study ID"], "rows": [["phs002431"]]}, "phs002431", {"Male"})


def test_missing_or_incomplete_grid_is_not_ready():
    assert not C3DC._participant_snapshot_matches_filters({}, "phs002431", {"Male"})
    assert not C3DC._participant_snapshot_matches_filters(snapshot(), "phs002431", {"Male"})
    data = snapshot("Male")
    data["rows"][0] = ["", "P0", "phs002431"]
    assert not C3DC._participant_snapshot_matches_filters(data, "phs002431", {"Male"})
