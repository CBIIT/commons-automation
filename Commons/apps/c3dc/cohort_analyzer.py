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
        label = item.locator(f"xpath={app.repo.xpath('CohortAnalyzer/ItemFullLabel')}").text_content().strip()
        match = re.search(r'\(([\d,]+)\)$', label)
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
    observe_analyzer_canvas(app)
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



# ---------------------------------------------------------------------------
# Shared selectors, evidence, and independent cohort baselines
# ---------------------------------------------------------------------------

def _element(app, key, scope=None):
    """Resolve Analyzer controls centrally; names and values stay in the workbook."""
    return (scope or app.page).locator(f"xpath={app.repo.xpath('CohortAnalyzer/' + key)}")


def _record(app, check, detail):
    app.results.append({'check': 'Analyzer ' + check, 'status': 'PASSED', 'detail': str(detail)})
    action_log.ui_action(f'Analyzer {check}: {detail}')


def _save_evidence(app, name, data):
    import json
    from pathlib import Path
    folder = getattr(app, '_analyzer_output', app.output_dir / 'cohort_analyzer')
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / (Path(name).stem + '.json')
    path.write_text(json.dumps(data, indent=2, default=list), encoding='utf-8')
    return path


def remember_analyzer_cohorts(app, report_name, include_metadata=''):
    """Snapshot popup membership before comparing Analyzer results.

    Optional metadata comes from each cohort's separate JSON export, rather
    than copying the table/chart under test into the expected data.
    """
    import json
    from pathlib import Path
    from Commons.apps.c3dc import cohort
    current = read_analyzer_cohorts(app)
    assert current, 'Create cohorts before recording an Analyzer baseline'
    app._analyzer_output = app.output_dir / Path(report_name).stem
    app._analyzer_snapshot = {}
    app._analyzer_metadata = {}
    app.open_explore()
    cohort.open_cohorts(app)
    for entry in current:
        cohort.select_cohort(app, entry.name)
        details = cohort.read_selected_cohort(app)
        assert details.participant_count == entry.participant_count
        app._analyzer_snapshot[entry.name] = details
        if include_metadata:
            path = cohort.download_cohort_metadata(app, report_name)
            metadata = json.loads(path.read_text(encoding='utf-8-sig'))
            records = {}
            for study in metadata[entry.name]:
                for consent in study.get('consent_groups', []):
                    for participant in consent.get('participants', []):
                        pair = (participant['participant_id'], study['dbgap_accession'])
                        records[pair] = participant
            assert set(records) == set(details.participants), 'Metadata differs from the cohort baseline'
            app._analyzer_metadata[entry.name] = records
    cohort.close_cohorts(app)
    open_cohort_analyzer(app)
    for entry in current:
        select_analyzer_cohort(app, entry.name, entry.selected)
    _save_evidence(app, 'cohort_baseline', {n: {'participants': s.participants, 'count': s.participant_count} for n, s in app._analyzer_snapshot.items()})


def _selected_sources(app):
    snapshot = getattr(app, '_analyzer_snapshot', None)
    assert snapshot, 'Record cohort membership before verifying Analyzer data'
    return {entry.name: snapshot[entry.name] for entry in read_analyzer_cohorts(app) if entry.selected}


def _expected_members(app):
    return set().union(*(set(source.participants) for source in _selected_sources(app).values()))


def select_analyzer_cohort(app, name, selected=True):
    """Select by its runtime name, keeping selection logic reusable for any cohort."""
    entries = {entry.name: entry for entry in read_analyzer_cohorts(app)}
    assert name in entries, f'Cohort not found: {name}'
    if entries[name].selected != selected:
        app.page.get_by_alt_text('checkbox ' + name, exact=True).click()
        app._analyzer_region = None
    expect(_element(app, 'Selector')).to_have_text(re.compile(
        rf'Cohort Selector\s*\({sum(e.selected for e in entries.values()) + (int(selected) - int(entries[name].selected))}/3\)'))
    assert next(e for e in read_analyzer_cohorts(app) if e.name == name).selected == selected


def verify_analyzer_empty_state(app):
    assert read_analyzer_cohorts(app) == ()
    expect(_element(app, 'Selector')).to_have_text(re.compile(r'Cohort Selector\s*\(0/3\)'))
    for key in ('AddChart', 'DownloadAll', 'ResetView'):
        expect(_element(app, key)).to_be_disabled()
    _element(app, 'TableView').click()
    _element(app, 'CreateCohort').click()
    assert read_analyzer_cohorts(app) == (), 'Empty results created a cohort'
    assert not _element(app, 'TableRows', _element(app, 'Table')).count()
    _element(app, 'ChartView').click()
    _record(app, 'empty state', 'No cohorts, zero selected, empty table and unavailable actions')


def verify_analyzer_existing_cohorts(app):
    sources = app._analyzer_snapshot
    for entry in read_analyzer_cohorts(app):
        select_analyzer_cohort(app, entry.name, True)
    actual = read_analyzer_cohorts(app)
    assert {e.name: e.participant_count for e in actual} == {n: s.participant_count for n, s in sources.items()}
    verify_analyzer_table(app)
    _record(app, 'existing cohorts', 'Names, counts and exact participant membership match Explore cohorts')


def verify_analyzer_selection(app):
    names = list(_selected_sources(app))
    for name in names:
        select_analyzer_cohort(app, name, False)
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
    failures_before = len(app.failures)
    for name in names:
        select_analyzer_cohort(app, name, True)
        try:
            verify_analyzer_table(app)
        except (AssertionError, PlaywrightTimeout) as error:
            selected = [entry.name for entry in read_analyzer_cohorts(app) if entry.selected]
            app._fail(f'Analyzer selected cohorts {selected}: {error}')
        _element(app, 'ChartView').click()
    if len(app.failures) == failures_before:
        _record(app, 'selection', 'One, two and three selected cohorts produce the correct participant union')


def verify_analyzer_selection_limit(app):
    """Create a fourth cohort in Explore, then test the Analyzer's three-selection cap."""
    from Commons.apps.c3dc import cohort
    before = read_analyzer_cohorts(app)
    assert len(before) == 3 and all(e.selected for e in before)
    app.open_explore(); cohort.open_cohorts(app)
    cohort.duplicate_selected_cohort(app)
    extra = cohort.read_selected_cohort(app)
    cohort.close_cohorts(app); open_cohort_analyzer(app)
    # Restore the same three selected sources in case navigation chose defaults.
    for entry in read_analyzer_cohorts(app):
        if entry.selected and entry.name == extra.name:
            select_analyzer_cohort(app, entry.name, False)
    for entry in before:
        select_analyzer_cohort(app, entry.name, True)
    app.page.get_by_alt_text('checkbox ' + extra.name, exact=True).click()
    assert sum(e.selected for e in read_analyzer_cohorts(app)) == 3
    assert not next(e for e in read_analyzer_cohorts(app) if e.name == extra.name).selected
    select_analyzer_cohort(app, before[0].name, False)
    select_analyzer_cohort(app, extra.name, True)
    assert sum(e.selected for e in read_analyzer_cohorts(app)) == 3
    _record(app, 'selection limit', 'Fourth selection rejected; succeeds after deselecting another cohort')


def verify_analyzer_sorting(app):
    """Check both sort controls with cohorts unselected and selected."""
    before = read_analyzer_cohorts(app)
    baseline = {e.name: e.participant_count for e in before}
    assert len(set(baseline.values())) > 1, 'Count sorting needs different cohort sizes'
    observations = []
    count_order = None
    failures_before = len(app.failures)
    # Establish the count control's default direction while nothing is selected;
    # selected cohorts must follow that same ordering. There is no reverse toggle.
    for selected in (False, True):
        for entry in read_analyzer_cohorts(app):
            select_analyzer_cohort(app, entry.name, selected)
        for key in ('SortAlphabetically', 'SortByCount'):
            _element(app, key).click()
            app.ui.wait_idle()
            actual = read_analyzer_cohorts(app)
            assert {e.name: e.participant_count for e in actual} == baseline
            assert all(e.selected == selected for e in actual), 'Sorting changed cohort selections'
            values = [e.name for e in actual] if key == 'SortAlphabetically' else [e.participant_count for e in actual]
            if key == 'SortAlphabetically':
                expected = sorted(baseline, key=str.casefold)
            elif count_order is None:
                ascending = sorted(baseline.values())
                assert values in (ascending, ascending[::-1]), f'Count order is incorrect: {values}'
                count_order = values
                expected = count_order
            else:
                expected = count_order
            observations.append({'control': key, 'selected': selected, 'expected': expected, 'actual': values})
            if values != expected:
                app._fail(f'Analyzer {key} (selected={selected}): expected {expected}, actual {values}')
    for entry in before:
        select_analyzer_cohort(app, entry.name, entry.selected)
    _save_evidence(app, 'cohort_sorting', observations)
    if len(app.failures) == failures_before:
        _record(app, 'sorting', 'A–Z and count sorting verified with cohorts unselected and selected')


# ---------------------------------------------------------------------------
# Table reading and participant verification
# ---------------------------------------------------------------------------

def _table_rows(app):
    return _element(app, 'TableRows', _element(app, 'Table')).evaluate_all(
        "rows => rows.map(row => Array.from(row.cells).map(cell => cell.innerText.trim()))")


def read_analyzer_table(app):
    """Read all pages with progress guards and restore page one afterwards."""
    if not _element(app, 'Table').is_visible():
        _element(app, 'TableView').click()
    container = _element(app, 'TableContainer')
    previous = _element(app, 'PreviousPage', container)
    next_page = _element(app, 'NextPage', container)
    def turn(button):
        first = _element(app, 'TableRows', _element(app, 'Table')).first
        old = first.inner_text()
        button.click()
        expect(first).not_to_have_text(old, timeout=app.ui.timeout_ms)

    expected = _result_members(app)
    _wait_for_analyzer_participants(app)
    expect(_element(app, 'PageRange', container)).to_have_text(re.compile(rf'\d+\s*-\s*\d+\s+of\s+{len(expected):,}'), timeout=app.ui.timeout_ms)
    while previous.is_enabled():
        turn(previous)
    if expected:
        page_size = int(_element(app, 'PageSize', container).inner_text().strip())
        expected_ids = [pair[0] for pair in expected]
        app.page.wait_for_function("""({xpath, ids, size}) => {
            const table = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
            if (!table) return false;
            const actual = Array.from(table.querySelectorAll('tbody tr td:first-child')).map(c=>c.innerText.trim());
            return actual.length === Math.min(size,ids.length) && actual.every(id=>ids.includes(id));
        }""", arg={'xpath': app.repo.xpath('CohortAnalyzer/Table'), 'ids': expected_ids, 'size': page_size}, timeout=app.ui.timeout_ms)
    rows, seen = [], set()
    while True:
        current = _table_rows(app)
        signature = tuple(tuple(r) for r in current)
        assert signature not in seen, 'Analyzer pagination repeated a page'
        seen.add(signature); rows.extend(current)
        if not next_page.is_enabled():
            break
        turn(next_page)
    while previous.is_enabled():
        turn(previous)
    return rows


def verify_analyzer_table(app):
    expected = _expected_members(app)
    rows = read_analyzer_table(app)
    actual = [(row[0], row[1]) for row in rows]
    assert len(actual) == len(set(actual)), 'Duplicate participant/study rows in Analyzer table'
    _save_evidence(app, 'participant_table', {'expected': sorted(expected), 'actual': actual, 'rows': rows})
    assert set(actual) == expected, f'Participant table mismatch: missing={expected-set(actual)}, unexpected={set(actual)-expected}'
    metadata = getattr(app, '_analyzer_metadata', {})
    for row in rows:
        pair = (row[0], row[1])
        sources = [records[pair] for records in metadata.values() if pair in records]
        if sources:
            participant = sources[0]
            assert set(re.split(r'[,;]\s*', row[2])) == set(participant.get('race') or ['Not Reported']), f'Race differs for {pair}: {row[2]!r}'
            assert row[3] == (participant.get('sex_at_birth') or 'Not Reported')
    _record(app, 'participant table', f'{len(actual)} exact participant/study pairs verified')


def verify_analyzer_pagination(app):
    original = read_analyzer_table(app)
    container = _element(app, 'TableContainer')
    page_size = _element(app, 'PageSize', container)
    current_size = page_size.inner_text().strip()
    page_size.click()
    options = app.page.get_by_role('option')
    values = [s.strip() for s in options.all_inner_texts()]
    sizes = [v for v in values if v.isdigit() and v != current_size]
    assert sizes, 'No alternative page size is available'
    options.filter(has_text=re.compile('^' + re.escape(sizes[0]) + '$')).click()
    changed = read_analyzer_table(app)
    assert sorted(changed) == sorted(original), 'Changing page size lost or changed records'
    _record(app, 'pagination', 'Forward/backward paging and alternate page size preserve every record')


# ---------------------------------------------------------------------------
# Canvas rendering and Venn comparison
# ---------------------------------------------------------------------------

# Canvas text is not in the accessibility tree. This observer records only the
# actual fillText calls, forwards them unchanged, and never reads React state.
_CANVAS_OBSERVER = """(() => {
  if (window.__caRenderedText) return;
  window.__caRenderedText = new WeakMap();
  const proto = CanvasRenderingContext2D.prototype;
  const clear = proto.clearRect, text = proto.fillText;
  proto.clearRect = function(...args) {
    window.__caRenderedText.set(this.canvas, []);
    return clear.apply(this, args);
  };
  proto.fillText = function(value, x, y, ...args) {
    const rows = window.__caRenderedText.get(this.canvas) || [];
    const transform = this.getTransform();
    rows.push({text: String(value), x: transform.a*x + transform.c*y + transform.e, y: transform.b*x + transform.d*y + transform.f});
    window.__caRenderedText.set(this.canvas, rows);
    return text.call(this, value, x, y, ...args);
  };
})();"""


def observe_analyzer_canvas(app):
    _observe_analyzer_responses(app)
    app.page.add_init_script(_CANVAS_OBSERVER)
    app.page.evaluate(_CANVAS_OBSERVER)



def _observe_analyzer_responses(app):
    """Observe request completion for readiness, never as an expected-data oracle."""
    if getattr(app, '_analyzer_observing', False) is True:
        return
    app._analyzer_responses = []
    app._analyzer_chart_responses = []
    def remember(response):
        if '/v1/graphql' not in response.url:
            return
        request = response.request.post_data_json or {}
        if 'cohortCharts' in request.get('query', ''):
            app._analyzer_chart_responses.append(response)
            app._analyzer_chart_responses = app._analyzer_chart_responses[-64:]
        if 'participantOverview' in request.get('query', '') and request.get('variables', {}).get('id'):
            app._analyzer_responses.append(response)
            app._analyzer_responses = app._analyzer_responses[-12:]
    app.page.on('response', remember)
    app._analyzer_observing = True


def _wait_for_analyzer_participants(app):
    """Wait for the lookup for the selected membership, excluding stale responses."""
    import time
    from playwright.sync_api import Error as PlaywrightError
    expected = _expected_members(app)
    if not expected:
        return
    deadline = time.monotonic() + app.ui.timeout_ms / 1000
    checked = {}
    while time.monotonic() < deadline:
        for response in reversed(app._analyzer_responses):
            if response not in checked:
                try:
                    response.finished()
                    rows = (response.json().get('data') or {}).get('participantOverview') or []
                    checked[response] = {(row['participant_id'], row['study_id']) for row in rows}
                except PlaywrightError:
                    checked[response] = None
            if checked[response] == expected:
                app.page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
                return
        app.page.wait_for_timeout(50)
    raise AssertionError(f'Analyzer participant lookup did not finish for the selected {len(expected)} source participants; observed response sizes={[len(v) if v is not None else None for v in checked.values()]}')



def _wait_for_analyzer_charts(app, expected_modes):
    """Wait for the response for the current aggregation choices, not old bars."""
    import time
    deadline = time.monotonic() + app.ui.timeout_ms / 1000
    metadata = getattr(app, '_analyzer_metadata', None)
    expected_ids = None
    if isinstance(metadata, dict) and metadata:
        names = _selected_sources(app)
        expected_ids = {record['id'] for name in names for record in metadata[name].values()}
    while time.monotonic() < deadline:
        for response in reversed(app._analyzer_chart_responses):
            variables = response.request.post_data_json.get('variables', {})
            ids = set().union(*(set(variables.get(key) or []) for key in ('c1', 'c2', 'c3')))
            if expected_ids is not None and ids != expected_ids:
                continue
            charts = variables.get('charts', [])
            modes = {chart['property']: chart['type'] for chart in charts}
            if all(modes.get(prop) == mode for prop, mode in expected_modes.items()):
                response.finished()
                app.ui.wait_idle()
                return
        app.page.wait_for_timeout(50)
    raise AssertionError(f'Chart response did not finish for aggregation modes {expected_modes}')


def _canvas_labels(app):
    return _element(app, 'Canvas').evaluate('(canvas) => window.__caRenderedText?.get(canvas) || []')


def _comparison_values(app, name, category):
    source = app._analyzer_snapshot[name]
    if category == 'Participant ID':
        return {pair[0] for pair in source.participants}
    records = app._analyzer_metadata.get(name)
    assert records, 'Record clinical metadata before Diagnosis or Treatment comparisons'
    values = set()
    for participant in records.values():
        if category == 'Diagnosis':
            values.update(d.get('diagnosis') or 'Not Reported' for d in participant.get('diagnoses', []))
        elif category == 'Treatment':
            for key in ('treatments_surgery', 'treatments_radiation', 'treatments_other', 'treatments_chemotherapy'):
                for treatment in participant.get(key, []):
                    field = 'chemotherapy_type' if key == 'treatments_chemotherapy' else 'treatment_type'
                    values.update(treatment.get(field) or [])
        else:
            raise ValueError(f'Unsupported Venn category: {category}')
    return values


def exclusive_regions(sets):
    """Compute mutually exclusive regions independently from the visualization."""
    result = {}
    for mask in range(1, 1 << len(sets)):
        included = [values for i, values in enumerate(sets) if mask & (1 << i)]
        excluded = [values for i, values in enumerate(sets) if not mask & (1 << i)]
        result[mask] = set.intersection(*included) - set().union(*excluded)
    return result


def choose_analyzer_category(app, category):
    _element(app, 'ChartView').click()
    radio = _element(app, 'VennCard').get_by_role('radio', name=category, exact=True)
    radio.check()
    expect(radio).to_be_checked()
    app._analyzer_category = category


def _venn_regions(app):
    """Identify diagram regions by their rendered geometry, not fixed pixels."""
    labels = _canvas_labels(app)
    numbers = [label for label in labels if re.fullmatch(r'\d[\d,]*', label['text'])]
    assert len(numbers) == 7, f'Expected seven numeric regions for three cohorts, got {numbers}'
    # The stylized diagram places A/B above C; intersections lie between them.
    a = min(numbers, key=lambda v: v['x']); b = max(numbers, key=lambda v: v['x'])
    c = max(numbers, key=lambda v: v['y'])
    middle = [v for v in numbers if v not in (a, b, c)]
    ab = min(middle, key=lambda v: v['y'])
    ac = min(middle, key=lambda v: v['x']); bc = max(middle, key=lambda v: v['x'])
    abc = next(v for v in middle if v not in (ab, ac, bc))
    return {1: a, 2: b, 4: c, 3: ab, 5: ac, 6: bc, 7: abc}


def verify_analyzer_comparison(app, category):
    _wait_for_analyzer_participants(app)
    choose_analyzer_category(app, category)
    sources = _selected_sources(app)
    assert len(sources) == 3, 'Select three cohorts before verifying Venn regions'
    canvas = _element(app, 'Canvas')
    expect(canvas).to_be_visible()
    app.page.wait_for_function("() => {const c=document.querySelector('canvas#canvas');return c && (window.__caRenderedText?.get(c)||[]).filter(v=>/^\\d[\\d,]*$/.test(v.text)).length===7 && window.__caRenderedText.get(c).some(v=>/^\\d[\\d,]*$/.test(v.text) && Number(v.text.replaceAll(',',''))>0);}", timeout=app.ui.timeout_ms)
    # Rendered names define A/B/C, so sidebar sorting never changes the oracle.
    labels = _canvas_labels(app)
    ordered = [next(name for name in sources if item['text'].startswith(name + ' ('))
               for item in labels if any(item['text'].startswith(name + ' (') for name in sources)]
    assert len(ordered) == len(set(ordered)) == 3, f'Incomplete rendered Venn labels: {labels}'
    expected = exclusive_regions([_comparison_values(app, n, category) for n in ordered])
    actual = _venn_regions(app)
    _save_evidence(app, 'venn_' + category.replace(' ', '_'), {
        'category': category, 'cohorts': ordered,
        'expected': {mask: sorted(values) for mask, values in expected.items()}, 'rendered': actual})
    assert {mask: int(label['text'].replace(',', '')) for mask, label in actual.items()} == {mask: len(values) for mask, values in expected.items()}, f'{category} Venn counts differ from cohort source data'
    app._analyzer_venn_order = ordered
    _record(app, category + ' comparison', 'All exclusive and overlapping Venn region counts verified')


def select_analyzer_region(app, mask):
    """Click a numeric region using its current canvas coordinates."""
    regions = _venn_regions(app)
    target = regions[int(mask)]
    assert int(target['text'].replace(',', '')) > 0, 'Choose a nonempty Venn region'
    canvas = _element(app, 'Canvas')
    size = canvas.evaluate('(c)=>({width:c.width,height:c.height})')
    box = canvas.bounding_box()
    canvas.click(position={'x': target['x'] * box['width'] / size['width'], 'y': target['y'] * box['height'] / size['height']})
    app._analyzer_region = None if getattr(app, '_analyzer_region', None) == int(mask) else int(mask)



def _result_members(app):
    mask = getattr(app, '_analyzer_region', None)
    if mask is None:
        return _expected_members(app)
    names = app._analyzer_venn_order
    ids = exclusive_regions([{p[0] for p in app._analyzer_snapshot[n].participants} for n in names])[mask]
    return {pair for pair in _expected_members(app) if pair[0] in ids}


def verify_analyzer_regions(app):
    verify_analyzer_comparison(app, 'Participant ID')
    ordered = app._analyzer_venn_order
    expected = exclusive_regions([{p[0] for p in app._analyzer_snapshot[name].participants} for name in ordered])
    nonempty = [mask for mask, values in expected.items() if values]
    assert any(mask in nonempty for mask in (1, 2, 4)), 'Baseline needs an exclusive region'
    assert any(mask in nonempty for mask in (3, 5, 6, 7)), 'Baseline needs an overlapping region'
    for mask in nonempty:
        _element(app, 'ChartView').click()
        select_analyzer_region(app, mask)
        rows = read_analyzer_table(app)
        assert {row[0] for row in rows} == expected[mask], f'Wrong table participants for Venn region {mask}'
        _element(app, 'ChartView').click()
        select_analyzer_region(app, mask)  # Clicking the same region clears it.
    verify_analyzer_table(app)
    _record(app, 'region selection', 'Exclusive/overlap selections and clearing verified against exact IDs')


# ---------------------------------------------------------------------------
# Chart controls and layout
# ---------------------------------------------------------------------------

def _histogram(app, title):
    """Scope every repeated chart control to its own visible card."""
    card = _element(app, 'HistogramCards').filter(has=app.page.locator('[data-ca-chart-title-text="true"]').filter(has_text=re.compile('^' + re.escape(title) + '$')))
    expect(card).to_have_count(1)
    return card


def _chart_titles(app):
    return _element(app, 'HistogramTitle', _element(app, 'HistogramCards')).all_text_contents()


def set_analyzer_chart_type(app, title, chart_type):
    card = _histogram(app, title)
    _element(app, 'ChartType', card).click()
    option = _element(app, 'ChartOptions').get_by_role('button', name=chart_type, exact=True)
    option.click()
    _element(app, 'ChartType', card).click()
    expect(_element(app, 'ChartOptions').get_by_role('button', name=chart_type, exact=True)).to_have_attribute('aria-selected', 'true')
    _element(app, 'ChartType', card).click()


def verify_analyzer_chart_types(app):
    titles = _chart_titles(app)
    assert titles, 'No histogram cards available'
    before = read_analyzer_cohorts(app)
    for title in titles:
        for chart_type in ('Stack Chart', 'Bar Chart'):
            set_analyzer_chart_type(app, title, chart_type)
            expect(_histogram(app, title).locator('.recharts-wrapper')).to_be_visible()
    assert read_analyzer_cohorts(app) == before
    _record(app, 'chart types', 'Bar/stack selection verified for every displayed histogram')


def add_analyzer_chart(app, title, location='top'):
    _element(app, 'AddChart' if location == 'top' else 'AddChartBelow').click()
    option = app.page.get_by_role('option', name=title, exact=True)
    expect(option).to_be_visible()
    option.click()
    chooser = app.page.get_by_role('listbox', name='Chart visualizations')
    expect(chooser).to_be_visible()
    chooser.get_by_role('option', name='Bar Chart', exact=True).click()
    expect(_histogram(app, title)).to_be_visible()


def verify_analyzer_chart_management(app):
    before = _chart_titles(app)
    _element(app, 'AddChart').click()
    available = app.page.get_by_role('option')
    labels = [v.strip() for v in available.all_inner_texts()]
    hidden = [v for v in labels if 'Displayed' not in v]
    assert hidden, 'No undisplayed chart available to add'
    title = hidden[0]
    available.filter(has_text=re.compile('^' + re.escape(title) + '$')).click()
    app.page.get_by_role('listbox', name='Chart visualizations').get_by_role('option', name='Bar Chart', exact=True).click()
    assert _chart_titles(app).count(title) == 1
    for key in ('AddChart', 'AddChartBelow'):
        expect(_element(app, key)).to_be_disabled()
    for i, old_title in enumerate(list(before) + [title]):
        card = _histogram(app, old_title)
        _element(app, 'HistogramRemove', card).click()
        expect(card).to_have_count(0)
        add_analyzer_chart(app, old_title, 'top' if i % 2 == 0 else 'bottom')
    assert set(_chart_titles(app)) == set(before + [title])
    _record(app, 'chart management', 'Add, prevent duplicate, remove and restore chart controls verified')


def verify_analyzer_layout_reset(app):
    titles = _chart_titles(app)
    assert len(titles) > 1
    first, second = _histogram(app, titles[0]), _histogram(app, titles[1])
    handle = first.get_by_role('button', name='Drag to reorder ' + titles[0] + ' card', exact=True)
    initial_positions = {title: _histogram(app, title).bounding_box() for title in titles}
    handle.drag_to(second)
    app.page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    positions = {title: _histogram(app, title).bounding_box() for title in titles}
    # Compare horizontal position in this row; scrolling must not look like a reorder.
    reordered = _chart_titles(app) != titles or any(abs(positions[t]['x'] - initial_positions[t]['x']) > 1 for t in titles)
    if not reordered:
        app._fail('Analyzer chart drag: dragging the first title onto the second card did not change their order or horizontal positions')
    card = _histogram(app, titles[0]); box = card.bounding_box()
    grip = card.locator('[title="Drag to resize chart"]').bounding_box()
    app.page.mouse.move(grip['x'] + grip['width']/2, grip['y'] + grip['height']/2)
    app.page.mouse.down()
    app.page.mouse.move(grip['x'] + grip['width']/2, grip['y'] + grip['height']/2 + box['height']/4, steps=8)
    app.page.mouse.up()
    resized = abs(card.bounding_box()['height'] - box['height']) > 1
    if not resized:
        app._fail('Analyzer chart resize: dragging the resize handle did not change chart height')
    _element(app, 'HistogramRemove', _histogram(app, titles[1])).click()
    expect(_element(app, 'HistogramCards').filter(has=app.page.locator('[data-ca-chart-title-text]').filter(has_text=re.compile('^'+re.escape(titles[1])+'$')))).to_have_count(0)
    reset = _element(app, 'ResetView')
    expect(reset).to_be_enabled(); reset.click()
    expect(_element(app, 'HistogramCards')).to_have_count(len(titles))
    actual_titles = _chart_titles(app)
    _save_evidence(app, 'chart_layout', {'before': initial_positions, 'after_drag': positions, 'reordered': reordered, 'resized': resized, 'expected_order': titles, 'reset_order': actual_titles})
    if actual_titles != titles:
        app._fail(f'Analyzer Reset View order: expected {titles}, actual {actual_titles}')
    for title, original in initial_positions.items():
        actual_height = _histogram(app, title).bounding_box()['height']
        if abs(actual_height - original['height']) > 1:
            app._fail(f'Analyzer Reset View height ({title}): expected {original["height"]}, actual {actual_height}')
    expect(reset).to_be_disabled()
    if reordered and resized and actual_titles == titles:
        _record(app, 'layout reset', 'Removed card, chart order and chart sizes restored to defaults')


def verify_analyzer_expanded_views(app):
    before = read_analyzer_cohorts(app)
    for key, text in (('ExpandVenn', 'Venn Diagrams'), ('ExpandSurvival', 'Survival Analysis')):
        _element(app, key).click()
        expect(app.page.get_by_role('button', name=text, exact=True)).to_be_visible()
        _element(app, 'ExpandedClose').click()
        expect(app.page.get_by_role('button', name=text, exact=True)).not_to_be_visible()
    for title in _chart_titles(app):
        card = _histogram(app, title)
        expect(card.locator('path.recharts-rectangle').first).to_be_visible(timeout=app.ui.timeout_ms)
        _element(app, 'HistogramExpand', card).click()
        expect(app.page.get_by_role('button', name=title, exact=True)).to_be_visible()
        _element(app, 'ExpandedClose').click()
    assert read_analyzer_cohorts(app) == before
    _record(app, 'expanded views', 'Venn, survival and histogram overlays open/close without changing selections')


def verify_analyzer_readme(app):
    before = read_analyzer_cohorts(app)
    _element(app, 'Readme').click()
    expect(app.page.get_by_text('USER GUIDE TOPICS', exact=True)).to_be_visible()
    topic = _element(app, 'ReadmeTopic')
    expect(topic).to_be_visible()
    topic.click()
    content = _element(app, 'ReadmeContent')
    expect(content.get_by_text('Cohort Analyzer Tutorial', exact=True)).to_be_visible()
    _element(app, 'ReadmeClose').click()
    assert read_analyzer_cohorts(app) == before
    _record(app, 'README', 'Guide content, Analyzer topic navigation and close verified')


# ---------------------------------------------------------------------------
# Downloads and export validation
# ---------------------------------------------------------------------------

def _download(app, trigger, label):
    from pathlib import Path
    with app.page.expect_download(timeout=app.ui.timeout_ms) as event:
        trigger.click()
    download = event.value
    assert download.failure() is None, f'Download failed: {download.failure()}'
    folder = getattr(app, '_analyzer_output', app.output_dir / 'cohort_analyzer') / label
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / Path(download.suggested_filename).name
    download.save_as(path)
    assert path.is_file() and path.stat().st_size, 'Empty or missing Analyzer download'
    return path


def _verify_image(path):
    from PIL import Image, ImageStat
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        assert image.width > 1 and image.height > 1, 'Export is not a chart-sized image'
        assert max(ImageStat.Stat(image.convert('RGB')).var) > 0, 'Exported image is blank'


def download_analyzer_all(app, fmt):
    _element(app, 'ChartView').click()
    # A visible bar proves that asynchronous chart data has rendered.
    expect(app.page.locator('path.recharts-rectangle').first).to_be_visible(timeout=app.ui.timeout_ms)
    _element(app, 'DownloadAll').click()
    return _download(app, app.page.get_by_role('menuitem', name=fmt, exact=True), 'all_' + fmt.lower())


def _read_chart_export(path):
    import csv
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t' if path.suffix == '.tsv' else ','))


def verify_analyzer_data_downloads(app):
    """Cross-check CSV/TSV and JSON and independently validate exported membership."""
    import json
    csv_path = download_analyzer_all(app, 'CSV')
    tsv_path = download_analyzer_all(app, 'TSV')
    csv_rows, tsv_rows = _read_chart_export(csv_path), _read_chart_export(tsv_path)
    assert csv_rows and csv_rows == tsv_rows, 'CSV/TSV chart data differ'
    path = download_analyzer_all(app, 'JSON'); payload = json.loads(path.read_text())
    sources = _selected_sources(app)
    assert set(payload['cohortLabels'].values()) == set(sources)
    metadata = app._analyzer_metadata
    assert metadata, 'Record cohort metadata before verifying JSON export GUIDs'
    for source in payload['cohorts']:
        records = metadata[source['cohortName']]
        expected = {record['id'] for record in records.values()}
        assert set(source['participantIds']) == expected, 'JSON export participant IDs differ from cohort membership'
    graph = payload['histogram']['graphData']
    properties = {'sex_at_birth': 'sexAtBirth', 'race': 'race', 'response': 'response', 'treatment_type': 'treatmentType'}
    for row in csv_rows:
        chart = graph[properties[row['chart_property']]]
        group = next(item for item in chart if item['name'] == row['group'])
        value_key = 'value' + chr(ord('A') + int(row['cohort'][1:]) - 1)
        assert float(row['subjects']) == float(group.get(value_key, 0)), 'CSV/JSON chart values differ'
    _record(app, 'all data downloads', 'CSV/TSV/JSON parse correctly; chart values agree and cohort GUID membership matches source metadata')


def verify_analyzer_image_downloads(app):
    png = download_analyzer_all(app, 'PNG'); _verify_image(png)
    pdf = download_analyzer_all(app, 'PDF')
    from pypdf import PdfReader
    reader = PdfReader(pdf)
    assert reader.pages and any(page.images for page in reader.pages), 'PDF has no chart images'
    _record(app, 'all image downloads', 'PNG decodes with nonblank content; PDF opens with chart images')


def verify_analyzer_venn_downloads(app):
    for category in ('Participant ID', 'Diagnosis', 'Treatment'):
        choose_analyzer_category(app, category)
        path = _download(app, _element(app, 'DownloadVenn'), 'venn_' + category.replace(' ', '_'))
        assert path.suffix.lower() == '.png'
        _verify_image(path)
    _record(app, 'Venn downloads', 'Nonblank PNG export verified for each matching category')


def verify_analyzer_histogram_downloads(app):
    for title in _chart_titles(app):
        card = _histogram(app, title)
        expect(card.locator('path.recharts-rectangle').first).to_be_visible(timeout=app.ui.timeout_ms)
        path = _download(app, _element(app, 'HistogramDownload', card), 'histogram_' + title.replace(' ', '_'))
        assert path.suffix.lower() == '.png'
        _verify_image(path)
    _record(app, 'histogram downloads', 'Every displayed histogram exports a valid nonblank PNG')


def verify_analyzer_survival_downloads(app):
    expect(_element(app, 'RiskTable').locator('tbody tr:first-child td').filter(has_text=re.compile(r'^\s*\d+\s*$')).first).to_be_visible(timeout=app.ui.timeout_ms)
    for name in ('Kaplan Meier Plot', 'Risk Table', 'Download Both'):
        _element(app, 'DownloadSurvival').click()
        trigger = app.page.get_by_role('menuitem', name=name, exact=True)
        path = _download(app, trigger, name.replace(' ', '_'))
        if path.suffix.lower() == '.png':
            _verify_image(path)
        else:
            from zipfile import ZipFile
            with ZipFile(path) as archive:
                names = archive.namelist()
                assert len(names) >= 2, 'Download Both must contain both survival artifacts'
    _record(app, 'survival downloads', 'Kaplan–Meier plot, risk table and combined export verified')


# ---------------------------------------------------------------------------
# Analyzer cohort removal and result actions
# ---------------------------------------------------------------------------

def verify_analyzer_removal(app, target, expected_message):
    """Cancel first, then confirm; verify both the membership and persisted list."""
    before = read_analyzer_cohorts(app)
    assert before and target in ('cohort', 'all')
    first = _element(app, 'Items').first
    trigger = _element(app, 'DeleteAll') if target == 'all' else _element(app, 'DeleteOne', first.locator(f"xpath={app.repo.xpath('CohortAnalyzer/SidebarRow')}"))
    removed = {e.name for e in before} if target == 'all' else {first.get_attribute('alt').removeprefix('checkbox ')}
    popup = app.page.locator(f"xpath={app.repo.xpath('Cohort/RemovalConfirmation')}")
    for confirm in (False, True):
        trigger.click()
        expect(popup).to_be_visible()
        message = popup.locator(f"xpath={app.repo.xpath('Cohort/RemovalMessage')}")
        expect(message).to_have_text(expected_message, use_inner_text=True)
        for name in ('Cancel', 'Confirm'):
            expect(popup.get_by_role('button', name=name, exact=True)).to_be_enabled()
        popup.get_by_role('button', name='Confirm' if confirm else 'Cancel', exact=True).click()
        expect(popup).not_to_be_visible()
        if not confirm:
            assert read_analyzer_cohorts(app) == before, 'Cancel changed the cohort list'
    expected_names = {e.name for e in before} - removed
    expect(_element(app, 'Items')).to_have_count(len(expected_names))
    app.page.reload(wait_until='domcontentloaded')
    expect(_element(app, 'AddExamples')).to_be_visible(timeout=app.ui.timeout_ms)
    assert {e.name for e in read_analyzer_cohorts(app)} == expected_names
    _record(app, target + ' removal', 'Confirmation text, Cancel, Confirm and persisted deletion verified')


def _export_participant_pairs(value, study=None):
    """Walk metadata exports without assuming a generated cohort name."""
    found = set()
    if isinstance(value, dict):
        study = value.get('dbgap_accession') or value.get('study_id') or study
        if value.get('participant_id'):
            assert study, 'Export participant has no study context'
            found.add((value['participant_id'], study))
        for child in value.values():
            if isinstance(child, (dict, list)):
                found.update(_export_participant_pairs(child, study))
    elif isinstance(value, list):
        for child in value:
            found.update(_export_participant_pairs(child, study))
    return found


def verify_analyzer_table_download(app, fmt):
    import json
    from Commons.apps.c3dc.cohort import _read_manifest_participants
    verify_analyzer_table(app)
    expected = _expected_members(app)
    _element(app, 'TableDownload').click()
    label = 'Manifest CSV' if fmt == 'CSV' else 'Metadata JSON'
    path = _download(app, app.page.get_by_text(re.compile('^' + re.escape(label) + '$', re.I)), 'table_' + fmt.lower())
    if fmt == 'CSV':
        records = _read_manifest_participants(path)
        actual = set(records)
    elif fmt == 'JSON':
        actual = _export_participant_pairs(json.loads(path.read_text(encoding='utf-8-sig')))
    else:
        raise ValueError('Table export format must be CSV or JSON')
    assert actual == expected, f'{fmt} export membership mismatch: missing={expected-actual}, unexpected={actual-expected}'
    _record(app, fmt + ' table download', f'{len(expected)} exact participants verified against cohort membership')


def create_analyzer_cohort_from_results(app):
    from Commons.apps.c3dc import cohort
    verify_analyzer_comparison(app, 'Participant ID')
    mask = next(mask for mask, item in _venn_regions(app).items() if int(item['text'].replace(',', '')) > 0)
    select_analyzer_region(app, mask)
    expected_ids = exclusive_regions([{p[0] for p in app._analyzer_snapshot[n].participants} for n in app._analyzer_venn_order])[mask]
    expected = {pair for source in app._analyzer_snapshot.values() for pair in source.participants if pair[0] in expected_ids}
    rows = read_analyzer_table(app)
    assert {(row[0], row[1]) for row in rows} == expected
    before = {e.name for e in read_analyzer_cohorts(app)}
    _element(app, 'CreateCohort').click()
    dialog = cohort.cohort_dialog(app)
    expect(dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}")).to_have_count(len(before) + 1, timeout=app.ui.timeout_ms)
    actual = cohort.read_selected_cohort(app)
    assert actual.name not in before, 'Creation reused an existing cohort instead of creating a new entry'
    assert set(actual.participants) == expected and actual.participant_count == len(expected)
    new_name = actual.name
    # Creation opens the shared editor; commit before checking persistence.
    dialog.locator(f"xpath={app.repo.xpath('Cohort/SaveChanges')}").click()
    app.page.reload(wait_until='domcontentloaded')
    expect(_element(app, 'AddExamples')).to_be_visible(timeout=app.ui.timeout_ms)
    assert {e.name for e in read_analyzer_cohorts(app)} == before | {new_name}, 'New cohort did not persist'
    _record(app, 'create from results', 'Created cohort contains exactly the selected Venn region participants')


def verify_analyzer_build_explore(app, expected_message):
    from Commons.apps.c3dc.cohort import _visible_participant_rows
    verify_analyzer_table(app)
    expected = {pair[0] for pair in _expected_members(app)}
    before = read_analyzer_cohorts(app)
    notice = _element(app, 'ExploreNotice')
    for confirm in (False, True):
        _element(app, 'BuildExplore').click()
        expect(notice).to_be_visible()
        expect(_element(app, 'ExploreNoticeMessage', notice)).to_have_text(expected_message)
        notice.get_by_role('button', name='Confirm' if confirm else 'Cancel', exact=True).click()
        if not confirm:
            expect(notice).not_to_be_visible()
            assert read_analyzer_cohorts(app) == before, 'Cancelling Explore navigation changed the comparison'
    expect(app.page).to_have_url(re.compile('/exploreParticipants'), timeout=app.ui.timeout_ms)
    # Explore's handoff URL is not a facet selection, so validate the rendered
    # filtered table directly rather than applying the cohort facet-wait rule.
    counter = app.page.locator(f"xpath={app.repo.xpath('Statbar/Participants-Count')}")
    expect(counter).to_have_text(f'{len(expected):,}', timeout=app.ui.timeout_ms)
    table = app.ui.visible(app.repo.xpath('ResultTabs/Participants-Tbl'))
    expect(table.locator('tbody tr').first).to_be_visible(timeout=app.ui.timeout_ms)
    app.page.wait_for_function("""({xpath, expected}) => {
        const root = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
        if (!root) return false;
        const headers = Array.from(root.querySelectorAll('thead th')).map(h=>h.innerText.trim());
        const column = headers.indexOf('Participant ID');
        const ids = Array.from(root.querySelectorAll('tbody tr')).map(row=>row.querySelectorAll('td')[column]?.innerText.trim());
        return ids.length > 0 && ids.every(id=>expected.includes(id));
    }""", arg={'xpath': app.repo.xpath('ResultTabs/Participants-Tbl'), 'expected': sorted(expected)}, timeout=app.ui.timeout_ms)
    actual, seen = set(), set()
    row_count = 0
    while True:
        ids = _visible_participant_rows(table)
        assert ids not in seen, 'Explore handoff pagination repeated a page'
        seen.add(ids); actual.update(ids); row_count += len(ids)
        next_page = table.locator(f"xpath={app.repo.xpath('Cohort/TopNextPage')}")
        if not next_page.is_enabled():
            break
        next_page.click()
        expect(table.locator('tbody tr:first-child')).not_to_contain_text(ids[0], timeout=app.ui.timeout_ms)
    assert row_count == len(expected), f'Explore handoff has {row_count} rows for {len(expected)} source participants'
    assert actual == expected, f'Explore handoff mismatch: missing={expected-actual}, unexpected={actual-expected}'
    _record(app, 'build in Explore', f'{len(expected)} exact participants carried into Explore')


def _metadata_chart_counts(records, property_name):
    """Count distinct participants per category; repeated visits cannot inflate bins."""
    counts = {}
    for pair, participant in records.items():
        values = set()
        if property_name in ('race', 'sex_at_birth'):
            raw = participant.get(property_name) or ['Not Reported']
            values.update(raw if isinstance(raw, list) else [raw])
        elif property_name == 'response':
            for response in participant.get('treatment_responses', []):
                values.update(response.get('response') or [])
        elif property_name == 'treatment_type':
            for key in ('treatments_surgery', 'treatments_radiation', 'treatments_other', 'treatments_chemotherapy'):
                for treatment in participant.get(key, []):
                    values.update(treatment.get('treatment_type') or [])
        else:
            raise ValueError(f'Unsupported histogram property: {property_name}')
        for value in values:
            counts.setdefault(value, set()).add(pair)
    return {value: len(members) for value, members in counts.items()}


def verify_analyzer_chart_values(app):
    """Verify count/percentage exports against independently downloaded metadata."""
    titles = _chart_titles(app)
    add_analyzer_chart(app, 'Treatment Type')
    properties = {'Sex at Birth': 'sex_at_birth', 'Race': 'race', 'Treatment Outcome': 'response', 'Treatment Type': 'treatment_type'}
    sources = _selected_sources(app)
    denominator = len(_expected_members(app))
    assert denominator
    comparisons = []
    modes = {
        prop: ('count' if _histogram(app, title).get_by_role('radio', name='# of Participants', exact=True).is_checked() else 'percentage')
        for title, prop in properties.items()
    }
    for mode, label in (('count', '# of Participants'), ('percentage', '% of Participants')):
        for title, prop in properties.items():
            radio = _histogram(app, title).get_by_role('radio', name=label, exact=True)
            radio.check(); expect(radio).to_be_checked()
            modes[prop] = mode
            # Serialize dependent changes; an earlier response must not overwrite
            # a later chart choice while several requests are still in flight.
            _wait_for_analyzer_charts(app, modes)
        rows = _read_chart_export(download_analyzer_all(app, 'CSV'))
        source_order = list(sources)
        for title, prop in properties.items():
            actual = {(row['group'], row['cohort']): float(row['subjects']) for row in rows if row['chart_property'] == prop}
            assert actual, f'No exported data for {title}'
            for i, name in enumerate(source_order, start=1):
                counts = _metadata_chart_counts(app._analyzer_metadata[name], prop)
                groups = {group for group, cohort in actual if cohort == f'c{i}'} | set(counts)
                for group in groups:
                    count = counts.get(group, 0)
                    expected = count if mode == 'count' else count / denominator * 100
                    value = actual.get((group, f'c{i}'), 0)
                    comparisons.append({'chart': title, 'mode': mode, 'cohort': name, 'category': group, 'expected': expected, 'actual': value})
                    if abs(value - expected) >= 1e-6:
                        app._fail(f'Analyzer {title} {mode}: {name}, {group}: expected {expected}, actual {value}')
    assert set(titles).issubset(_chart_titles(app))
    _save_evidence(app, 'chart_values', comparisons)
    if all(abs(row['actual']-row['expected']) < 1e-6 for row in comparisons):
        _record(app, 'counts and percentages', 'Every chart category compared with unique source participants in both aggregation modes')


def _survival_observations(records):
    """Derive follow-up duration from source ages, excluding missing sentinel ages."""
    observations = []
    for participant in records.values():
        ages = [d['age_at_diagnosis'] for d in participant.get('diagnoses', []) if isinstance(d.get('age_at_diagnosis'), (int, float)) and d['age_at_diagnosis'] >= 0]
        survivors = [s for s in participant.get('survivals', []) if isinstance(s.get('age_at_last_known_survival_status'), (int, float)) and s['age_at_last_known_survival_status'] >= 0 and s.get('last_known_survival_status') in ('Alive', 'Dead')]
        if ages and survivors:
            latest = max(survivors, key=lambda s: s['age_at_last_known_survival_status'])
            duration = latest['age_at_last_known_survival_status'] - min(ages)
            if duration >= 0:
                observations.append((duration, latest['last_known_survival_status'] == 'Dead'))
    return observations


def verify_analyzer_survival(app):
    table = _element(app, 'RiskTable')
    expect(table).to_be_visible(timeout=app.ui.timeout_ms)
    # The month headings define thresholds; no captured risk counts are stored.
    headings = table.locator('thead th').all_inner_texts()
    months = [int(re.search(r'\d+', h).group()) for h in headings if re.search(r'\d+', h)]
    assert months, 'Survival risk table has no month headings'
    rows = table.locator('tbody tr')
    sources = _selected_sources(app)
    expect(rows).to_have_count(len(sources))
    evidence = []
    for row, name in zip(rows.all(), sources):
        observations = _survival_observations(app._analyzer_metadata[name])
        assert observations, f'No source survival observations for {name}'
        actual = [int(cell.strip().replace(',', '')) for cell in row.locator('td').all_inner_texts() if cell.strip().replace(',', '').isdigit()]
        expected = [sum(duration >= month * 30 for duration, _ in observations) for month in months]
        evidence.append({'cohort': name, 'months': months, 'expected': expected, 'actual': actual})
        if actual != expected:
            app._fail(f'Analyzer survival risk table ({name}): months={months}, expected={expected}, actual={actual}')
    _save_evidence(app, 'survival_risk_table', evidence)
    if all(row['actual'] == row['expected'] for row in evidence):
        _record(app, 'survival analysis', 'Risk-table counts compared with source follow-up durations')


def verify_analyzer_tooltip(app, control, expected_text):
    """Check documented native/HTML tooltips while preserving cohort selections."""
    before = read_analyzer_cohorts(app)
    target = _element(app, control)
    expect(target).to_have_count(1)
    target.hover()
    title = target.get_attribute('title')
    if title is not None:
        assert title == expected_text, f'{control} tooltip differs: {title!r}'
    else:
        tooltip = app.page.get_by_role('tooltip').filter(has_text=expected_text)
        expect(tooltip).to_be_visible()
        expect(tooltip).to_have_text(expected_text)
    _element(app, 'Readme').hover()
    assert read_analyzer_cohorts(app) == before
    _record(app, 'tooltip ' + control, expected_text)
