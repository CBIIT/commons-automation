"""Cohort Analyzer navigation and reusable UI verification helpers."""

from dataclasses import dataclass
import re

from playwright.sync_api import expect

from Commons import action_log


# ---------------------------------------------------------------------------
# Analyzer cohort details
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AnalyzerCohort:
    name: str
    participant_count: int
    selected: bool


def read_analyzer_cohorts(app):
    """Read each sidebar entry once, avoiding duplicated overflow-tooltip labels."""
    items = app.page.locator(app.repo.xpath('CohortAnalyzer/Items'))
    cohorts = []
    for item in items.all():
        name = item.get_attribute('alt').removeprefix('checkbox ')
        label = item.locator(f"xpath={app.repo.xpath('CohortAnalyzer/ItemLabel')}").text_content().strip()
        match = re.fullmatch(rf'{re.escape(name)}\s*\(([\d,]+)\)', label)
        assert match, f'Analyzer cohort label has no participant count: {label!r}'
        cohorts.append(AnalyzerCohort(
            name, int(match.group(1).replace(',', '')),
            bool(re.search(r'/tickIcon\.', item.get_attribute('src') or '')),
        ))
    return tuple(cohorts)


# ---------------------------------------------------------------------------
# Navigation and example cohort creation
# ---------------------------------------------------------------------------

def open_cohort_analyzer(app):
    """Navigate using the application's Cohort Analyzer navigation link."""
    app._example_cohorts_added = False
    app.click('CohortAnalyzer/Navigation')
    expect(app.page).to_have_url(re.compile(r'/cohortAnalyzer/?(?:[?#].*)?$'))
    expect(app.page.locator(app.repo.xpath('CohortAnalyzer/AddExamples'))).to_be_visible(timeout=app.ui.timeout_ms)
    expect(app.page.locator(app.repo.xpath('CohortAnalyzer/Selector'))).to_be_visible()
    action_log.ui_action('Cohort Analyzer opened successfully.')


def add_example_cohorts(app):
    """Click Add Example Cohorts once and require three entries to appear.

    This first creation testcase starts with an empty browser context. Refuse
    existing entries rather than replacing cohorts and mistaking them for new ones.
    """
    app._example_cohorts_added = False
    items = app.page.locator(app.repo.xpath('CohortAnalyzer/Items'))
    expect(items).to_have_count(0)
    selector = app.page.locator(app.repo.xpath('CohortAnalyzer/Selector'))
    expect(selector).to_have_text(re.compile(r'Cohort Selector\s*\(0/3\)'))
    app.click('CohortAnalyzer/AddExamples')
    expect(items).to_have_count(3, timeout=app.ui.timeout_ms)
    expect(selector).to_have_text(re.compile(r'Cohort Selector\s*\(3/3\)'))
    app._example_cohorts_added = True
    action_log.ui_action('Clicked Add Example Cohorts once; three cohort entries appeared.')


def _example_cohort_checks(cohorts, expected_names):
    """Require actual distinct, populated and selected cohorts, not only a counter."""
    names = [cohort.name for cohort in cohorts]
    return {
        'three cohort entries': len(cohorts) == 3,
        'three distinct cohort names': len(set(names)) == 3,
        'expected example names': set(names) == set(expected_names),
        'nonempty participant counts': bool(cohorts) and all(cohort.participant_count > 0 for cohort in cohorts),
        'all example cohorts selected': bool(cohorts) and all(cohort.selected for cohort in cohorts),
    }


def verify_example_cohorts_created(app, expected_names):
    """Verify the three expected examples and their selected, populated entries."""
    if not getattr(app, '_example_cohorts_added', False):
        raise AssertionError('Add example cohorts before verifying their creation')
    names = tuple(name.strip() for name in expected_names.split(';') if name.strip())
    if len(names) != 3 or len(set(names)) != 3:
        raise ValueError('Provide three distinct expected cohort names separated by semicolons')
    cohorts = read_analyzer_cohorts(app)
    checks = _example_cohort_checks(cohorts, names)
    detail = '; '.join(f'{cohort.name} ({cohort.participant_count})' for cohort in cohorts)
    for check, passed in checks.items():
        if passed:
            app.results.append({'check': f'Analyzer {check}', 'status': 'PASSED', 'detail': detail})
        else:
            app._fail(f'Analyzer {check} failed: {detail}; expected names={names}')
    expect(app.page.locator(app.repo.xpath('CohortAnalyzer/Selector'))).to_have_text(re.compile(r'Cohort Selector\s*\(3/3\)'))
    if all(checks.values()):
        action_log.ui_action(f'Created and selected all three example cohorts: {detail}.')

