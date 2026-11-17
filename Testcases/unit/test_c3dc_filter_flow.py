"""C3DC applies testcase filters before reading result tables."""
from unittest.mock import Mock, MagicMock

import pytest

from Commons.apps.c3dc import C3DC
from Commons.base_app import BaseApp

pytestmark = pytest.mark.unit


def test_study_and_demographic_filters_do_not_read_or_poll_the_table(monkeypatch):
    app = C3DC.__new__(C3DC)
    app.page, app.ui, app.repo = MagicMock(), Mock(), Mock()
    app.repo.filter_group.return_value.checkbox_xpath.side_effect = lambda value: f"//*[@id='checkbox_Facet_{value}']"
    app.read_results_table = Mock()
    filters = []
    monkeypatch.setattr(BaseApp, 'select_filter', lambda _, group, value: filters.append((group, value)))
    monkeypatch.setattr(BaseApp, 'verify_tab', lambda self, name: self.read_results_table(self.TABS[name]))

    app.select_filter('Study/dbGaP_Accession', 'phs000463')
    app.select_filter('Demographics/SexAtBirth', 'Female')

    assert filters == [('Study/dbGaP_Accession', 'phs000463'), ('Demographics/SexAtBirth', 'Female')]
    assert app._active_study_accession == 'phs000463'
    app.read_results_table.assert_not_called()
    app.page.evaluate.assert_not_called()
    assert [call.args[0] for call in app.page.locator.call_args_list] == ['#statsbar_count_1', '#statsbar_count_1']

    app.verify_tab('Participants')
    app.read_results_table.assert_called_once_with(C3DC.TABS['Participants'])


@pytest.mark.parametrize("retired", sorted(C3DC.RETIRED_RESULT_TABS))
def test_retired_result_tab_is_reported_without_reading_ui_or_database(retired):
    app = C3DC.__new__(C3DC)
    app.results = []
    app.open_tab, app.read_results_table, app.source = Mock(), Mock(), Mock()

    app.verify_tab(retired)

    assert app.results == [{"check": retired, "status": "SKIPPED",
                            "detail": "result tab removed from C3DC Explore"}]
    app.open_tab.assert_not_called()
    app.read_results_table.assert_not_called()
    assert app.source.mock_calls == []


def test_current_result_tabs_still_dispatch_to_shared_verification(monkeypatch):
    from Commons.tab_setting import settings_for_app

    app = C3DC.__new__(C3DC)
    verify = Mock()
    monkeypatch.setattr(BaseApp, "verify_tab", verify)
    configured = settings_for_app("C3DC").tab_execution
    assert set(configured) == set(C3DC.STANDARD_VERIFY_TABS + C3DC.EXPLORE_FILE_TABS)
    for label in configured:
        app.verify_tab(label)
    assert [call.args[0] for call in verify.call_args_list] == [
        "Participants", "Studies", "GeneticAnalysis", "Samples", "Files", "ImagingData",
    ]
    assert set(C3DC.TABS) == {call.args[0] for call in verify.call_args_list}


def test_unknown_result_tab_is_not_silently_skipped():
    app = C3DC.__new__(C3DC)
    with pytest.raises(KeyError, match="Misspelled tab"):
        app.verify_tab("Misspelled tab")


@pytest.mark.parametrize("label", ["Participants", "Studies", "Genetic Analysis", "Samples"])
def test_select_current_tab_directly_without_more_menu(label):
    app = C3DC.__new__(C3DC)
    app.ui = Mock()
    tabs = ["Participants (100)", "Studies (1)", "Genetic Analysis (10)", "Samples (20)"]
    def locator(xpath):
        node = Mock()
        if xpath == app.RESULT_TAB_BUTTONS_XP:
            node.count.return_value = len(tabs)
        else:
            index = int(xpath.rsplit("[", 1)[1].rstrip("]")) - 1
            node.evaluate.return_value = tabs[index]
        return node
    app.ui.loc.side_effect = locator

    assert app._select_result_tab(label)
    app.ui.js_click.assert_called_once_with(
        f"({app.RESULT_TAB_BUTTONS_XP})[{[t.split(' (')[0] for t in tabs].index(label) + 1}]",
        repo_key=f"ResultTabs/selectTab-{label}",
    )
    app.ui.wait_visible.assert_called_once_with(
        f"({app.RESULT_TAB_BUTTONS_XP})[1]", timeout_ms=10000,
    )


def test_filter_readiness_waits_for_the_selected_search_response(monkeypatch):
    import json
    app = C3DC.__new__(C3DC)
    app.page, app.repo, app.ui = MagicMock(), Mock(), Mock()
    app.repo.filter_group.return_value.checkbox_xpath.return_value = "//*[@id='checkbox_Race_Black or African American']"
    events = []
    monkeypatch.setattr(BaseApp, "select_filter", lambda *_: events.append("filter"))
    app.page.expect_response.return_value.__enter__.return_value.value.body.side_effect = lambda: events.append("response")
    app._wait_explore_results_ready = lambda: events.append("readiness")

    app.select_filter("Demographics/Race", "BlkAfricAmer")

    assert events == ["filter", "response", "readiness"]
    predicate = app.page.expect_response.call_args.args[0]
    response = Mock(url="https://clinicalcommons-qa.ccdi.cancer.gov/v1/graphql/")
    response.request.post_data = json.dumps({"operationName": "search", "variables": {"race": ["Black or African American"]}})
    assert predicate(response)
    response.request.post_data = json.dumps({"operationName": "search", "variables": {"race": ["White"]}})
    assert not predicate(response)


def test_reopening_selected_result_tab_preserves_explicit_sort():
    app = C3DC.__new__(C3DC)
    app.ui = Mock()
    selected = app.ui.loc.return_value
    selected.count.return_value = 1
    selected.first.inner_text.return_value = "Genetic Analyses (100)"

    app.open_tab("GeneticAnalysis")

    app.ui.js_click.assert_not_called()


@pytest.mark.parametrize("already_sorted", [False, True])
def test_sort_result_tab_waits_for_ordered_rows(already_sorted):
    app = C3DC.__new__(C3DC)
    app.page, app.repo, app.ui = Mock(), Mock(), Mock()
    app.open_tab = Mock()
    app.repo.xpath.side_effect = lambda key: "//column" if key.endswith("-Colm") else "//table"
    label = app.ui.loc.return_value
    label.get_attribute.return_value = "MuiTableSortLabel-active" if already_sorted else ""
    label.locator.return_value.count.return_value = int(already_sorted)
    label.evaluate.return_value = 1

    app.sort_result_tab("GeneticAnalysis", "ResultTabs/SortByGeneticAnalysisID-Colm")

    assert app.ui.click.call_count == int(not already_sorted)
    app.page.wait_for_function.assert_called_once()
    assert app.page.wait_for_function.call_args.kwargs["arg"] == {"table": "//table", "index": 1}
