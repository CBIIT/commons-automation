"""Reusable Upload Participants Set controls for Explore and Analyzer workflows."""
from dataclasses import dataclass
import csv
from pathlib import Path
import json
import re
from uuid import uuid4
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import expect

from Commons import action_log


@dataclass(frozen=True)
class ParticipantUpload:
    """Independent input and expected match membership for an upload."""
    matched: tuple[str, ...]
    unmatched: tuple[str, ...] = ()

    @property
    def submitted(self):
        return self.matched + self.unmatched


def _control(app, name, scope=None):
    return (scope or app.page).locator(f"xpath={app.repo.xpath('UploadParticipants/' + name)}")


def _dialog(app):
    dialog = _control(app, 'Dialog')
    expect(dialog).to_be_visible(timeout=app.ui.timeout_ms)
    return dialog


# ---------------------------------------------------------------------------
# Small UI actions: callers supply IDs, file paths or the requested control.
# ---------------------------------------------------------------------------

def open_participant_upload(app):
    """Open a new upload or reopen the currently applied participant set."""
    # Upload lives inside the facet drawer, which is closed in a fresh session.
    if not _control(app, 'Open').is_visible():
        _control(app, 'FacetPanel').click()
    _control(app, 'Open').click()
    dialog = _dialog(app)
    action_log.ui_action('Upload Participants Set opened.')
    return dialog


def type_participant_ids(app, participant_ids, separator=','):
    """Accept literal text or an iterable; preserve caller formatting for validation."""
    text = participant_ids if isinstance(participant_ids, str) else separator.join(participant_ids)
    _control(app, 'Ids', _dialog(app)).fill(text)


def format_participant_ids(participant_ids, separator=',\n', repetitions=2, padding=' ', trailing_separator=True):
    """Build a formatted draft without altering ID case or expected membership."""
    ids = tuple(participant_ids)
    if not ids or repetitions < 1:
        raise ValueError('Provide participant IDs and a positive repetition count')
    text = separator.join(f'{padding}{value}{padding}' for value in ids * repetitions)
    return text + (separator if trailing_separator else '')


def type_formatted_participant_ids(app, participant_ids, repetitions=2):
    """Enter repeated IDs with surrounding spaces, line breaks and a trailing comma."""
    text = format_participant_ids(participant_ids, repetitions=repetitions)
    type_participant_ids(app, text)
    return text


def verify_participant_upload_draft(app, participant_ids, separator=','):
    """Verify the reopened input retains exactly the caller's submitted text."""
    text = participant_ids if isinstance(participant_ids, str) else separator.join(participant_ids)
    expect(_control(app, 'Ids', _dialog(app))).to_have_value(text)
    action_log.ui_action('Reopened participant set retains the submitted IDs.')


def write_participant_file(path, participant_ids, separator='\n'):
    """Write UTF-8 text or a headerless CSV row, preserving IDs as strings."""
    if isinstance(participant_ids, str):
        raise TypeError('Pass a sequence of IDs, not a single string')
    ids = tuple(participant_ids)
    if not ids or not all(isinstance(value, str) and value for value in ids):
        raise ValueError('Provide at least one nonempty participant ID')
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.suffix.lower() == '.csv':
        with target.open('w', encoding='utf-8', newline='') as stream:
            csv.writer(stream).writerow(ids)
    else:
        target.write_text(separator.join(ids) + separator, encoding='utf-8')
    return target


def attach_participant_file(app, path):
    """Select a local file without a native file-picker dependency."""
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    _control(app, 'File', _dialog(app)).set_input_files(str(source))
    action_log.ui_action(f'Attached participant file: {source.name}.')


def clear_participant_upload(app):
    """Clear the current draft and wait for the dialog to close."""
    dialog = _dialog(app)
    _control(app, 'Clear', dialog).click()
    expect(dialog).not_to_be_visible()


def cancel_participant_upload(app):
    dialog = _dialog(app)
    _control(app, 'Cancel', dialog).click()
    expect(dialog).not_to_be_visible()


def submit_participant_upload(app):
    dialog = _dialog(app)
    _control(app, 'Submit', dialog).click()
    expect(dialog).not_to_be_visible(timeout=app.ui.timeout_ms)


# ---------------------------------------------------------------------------
# Matching preview and exact membership checks
# ---------------------------------------------------------------------------

def read_upload_summary(app, status):
    """Expand a matched/unmatched section and return its IDs, not just its count."""
    if status not in ('matched', 'unmatched'):
        raise ValueError('status must be matched or unmatched')
    dialog = _dialog(app)
    prefix = status.title()
    count = int(_control(app, prefix + 'Count', dialog).inner_text().replace(',', ''))
    if count == 0:
        return ()
    details = _control(app, prefix + 'Table', dialog)
    if not details.is_visible():
        _control(app, prefix, dialog).click()
    expect(details).to_be_visible(timeout=app.ui.timeout_ms)
    lines = details.inner_text().splitlines()
    return tuple(line.strip() for line in lines if line.strip() and line.strip() != 'Submitted Participant ID')


def verify_upload_preview(app, expected):
    """Compare both preview lists and deduplicated totals with caller expectations."""
    dialog = _dialog(app)
    submitted = len(set(expected.submitted))
    message = rf'{submitted} submitted Participant IDs mapped to {len(set(expected.matched))} unique CCDI Participant IDs'
    expect(dialog).to_contain_text(re.compile(message), timeout=app.ui.timeout_ms)
    actual = {key: read_upload_summary(app, key) for key in ('matched', 'unmatched')}
    for key, values in actual.items():
        wanted = getattr(expected, key)
        assert len(values) == len(set(wanted)), f'{key} preview count differs: {values}'
        assert set(values) == set(wanted), f'{key} preview: expected {wanted}, actual {values}'
    action_log.ui_action('Participant upload preview: exact matched and unmatched IDs verified.')
    return actual


def _explore_ids(app):
    from Commons.apps.c3dc.cohort import _visible_participant_rows
    table = app.ui.visible(app.repo.xpath('ResultTabs/Participants-Tbl'))
    return _visible_participant_rows(table)


def prepare_participant_upload(app, count=2, unmatched_count=1):
    """Choose study-submitted IDs from Explore, retaining an independent baseline.

    Lowercase CPI identifiers displayed in Explore are distinct from the source
    IDs accepted by this upload. This happy-path fixture uses source-style IDs;
    CPI mapping belongs in a separate validation testcase.
    """
    if count < 1 or unmatched_count < 0:
        raise ValueError('count must be positive and unmatched_count nonnegative')
    app.open_tab('Participants')
    expect(_control(app, 'ExploreRows').first).to_be_visible(timeout=app.ui.timeout_ms)
    ids = tuple(dict.fromkeys(value for value in _explore_ids(app) if value == value.upper()))[:count]
    assert len(ids) == count, f'Need {count} source-style IDs on the current Explore page; found {ids}'
    unknown = tuple('AUTOTEST-' + uuid4().hex.upper() for _ in range(unmatched_count))
    action_log.ui_action(f'Prepared upload: {len(ids)} source IDs and {len(unknown)} unmatched IDs.')
    return ParticipantUpload(ids, unknown)


def prepare_participant_upload_update(app, count=2, unmatched_count=1):
    """Capture two disjoint source sets before the first upload filters Explore."""
    pool = prepare_participant_upload(app, count * 2, unmatched_count * 2)
    original = ParticipantUpload(pool.matched[:count], pool.unmatched[:unmatched_count])
    replacement = ParticipantUpload(pool.matched[count:], pool.unmatched[unmatched_count:])
    return original, replacement


def read_uploaded_participant_ids(app, expected_count):
    """Read the full uploaded result set, guarding against repeated pages."""
    container = app.ui.visible(app.repo.xpath('ResultTabs/Participants-Tbl'))
    previous = _control(app, 'PreviousPage', container)
    while previous.is_enabled():
        old = _explore_ids(app)
        previous.click()
        expect(_control(app, 'ExploreRows').first).not_to_contain_text(old[0])
    ids = []
    for _ in range(expected_count + 1):
        page = _explore_ids(app)
        assert not set(page).intersection(ids), 'Pagination repeated participant IDs'
        ids.extend(page)
        assert len(ids) <= expected_count, 'Results include additional participants'
        next_page = _control(app, 'NextPage', container)
        if not next_page.is_enabled():
            return tuple(ids)
        next_page.click()
        expect(_control(app, 'ExploreRows').first).not_to_contain_text(page[0])
    raise AssertionError('Uploaded participant pagination did not finish')


def verify_uploaded_participants(app, participant_ids, report_name='participant_upload'):
    """Require exact Explore membership and stat count after a submitted upload.

    Waiting for the actual row set avoids accepting stale rows while the stat
    bar has already updated. Pagination reuses the cohort participant row parser.
    """
    expected = set(participant_ids)
    assert expected, 'Use a nonempty expected set for submitted-result verification'
    app.open_tab('Participants')
    table_xpath = app.repo.xpath('ResultTabs/Participants-Tbl')
    app.page.wait_for_function("""({xpath, ids}) => {
      const root = document.evaluate(xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
      if (!root) return false;
      const headers = [...root.querySelectorAll('thead th')].map(e=>e.innerText.trim());
      const col = headers.indexOf('Participant ID');
      const values = [...root.querySelectorAll('tbody tr')].map(r=>r.cells[col]?.innerText.trim()).filter(Boolean);
      return values.length > 0 && values.every(id=>ids.includes(id));
    }""", arg={'xpath': table_xpath, 'ids': sorted(expected)}, timeout=app.ui.timeout_ms)
    expect(app.page.locator(app.repo.xpath('Statbar/Participants-Count'))).to_have_text(f'{len(expected):,}', timeout=app.ui.timeout_ms)
    actual = read_uploaded_participant_ids(app, len(expected))
    assert len(actual) == len(expected) and set(actual) == expected, f'Uploaded results differ: expected {sorted(expected)}, actual {actual}'
    expect(_control(app, 'View')).to_be_visible()
    folder = app.output_dir / Path(report_name).stem
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'participant_upload.json').write_text(json.dumps({'expected': sorted(expected), 'actual': list(actual)}, indent=2))
    app.results.append({'check': 'Participant set upload', 'status': 'PASSED', 'detail': f'Exact membership verified for {len(expected)} participants'})
    action_log.ui_action(f'Uploaded participant set verified: {len(expected)} exact participant IDs.')


# ---------------------------------------------------------------------------
# Participant limit boundaries (the limit is supplied by the testcase).
# ---------------------------------------------------------------------------

def fetch_upload_source_ids(app, count):
    """Reuse the UI's participant lookup request to prepare a file without paging."""
    expect(_control(app, 'ExploreRows').first).to_be_visible(timeout=app.ui.timeout_ms)
    observed = getattr(app, '_cohort_participant_response', None)
    assert observed, 'Open Explore before preparing the upload file'
    request = observed[0].request
    payload = json.loads(request.post_data)
    variables = payload.setdefault('variables', {})
    direction = str(variables.get('sort_direction', 'asc'))
    variables.update(first=count * 2, offset=0, sort_direction='DESC' if direction.isupper() else 'desc')
    response = app.page.request.post(request.url, data=payload)
    assert response.ok, f'Participant fixture request failed: HTTP {response.status}'
    data = response.json()
    assert not data.get('errors'), f'Participant fixture lookup failed: {data.get("errors")}'
    rows = (data.get('data') or {}).get('participantOverview') or []
    ids = tuple(dict.fromkeys(row['participant_id'] for row in rows if row['participant_id'] == row['participant_id'].upper()))
    assert len(ids) >= count, f'Need {count} source IDs; lookup returned {len(ids)}'
    return ids[:count]


def _upload_boundary_file(app, expected, folder, label, reset=False):
    open_participant_upload(app)
    if reset:
        clear_participant_upload(app)
        open_participant_upload(app)
    path = write_participant_file(folder / f'{label}.txt', expected.submitted)
    attach_participant_file(app, path)


def verify_uploaded_participant_count(app, count):
    """Verify an applied set using its stat count and View Participants Set control."""
    expect(app.page.locator(app.repo.xpath('Statbar/Participants-Count'))).to_have_text(f'{count:,}', timeout=app.ui.timeout_ms)
    expect(_control(app, 'View')).to_be_visible()
    action_log.ui_action(f'Uploaded participant stat count verified: {count}.')


def verify_upload_limit_rejected(app, limit, folder):
    """Require limit feedback and prevent the over-limit set from being applied."""
    dialog = _dialog(app)
    submit = _control(app, 'Submit', dialog)
    # Give client-side validation an opportunity to finish before Submit.
    app.ui.wait_idle()
    if submit.is_enabled():
        submit.click()
        app.ui.wait_idle()
    xpath = app.repo.xpath('UploadParticipants/LimitFeedback').format(limit=limit, formatted_limit=f'{limit:,}')
    feedback = app.page.locator(f'xpath={xpath}')
    try:
        expect(dialog).to_be_visible()
        expect(feedback).to_be_visible(timeout=app.ui.timeout_ms)
        message = feedback.inner_text()
        assert re.search(rf'\b{limit:,}\b|\b{limit}\b', message), message
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'limit_validation.json').write_text(json.dumps({'limit': limit, 'message': message}, indent=2), encoding='utf-8')
    except AssertionError as error:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'limit_failure.txt').write_text(app.page.locator('body').inner_text(), encoding='utf-8')
        actual_count = app.page.locator(app.repo.xpath('Statbar/Participants-Count')).inner_text()
        app._fail(f'Upload limit ({folder.name}, maximum {limit}): over-limit input was not rejected with visible validation. Observed participant count: {actual_count}. {error}')
    finally:
        if dialog.is_visible():
            cancel_participant_upload(app)


def verify_participant_upload_limit(app, limit, report_name):
    """Test the inclusive text-file limit and one-over boundary, without table reads."""
    if limit < 1:
        raise ValueError('Provide a positive limit')
    ids = fetch_upload_source_ids(app, limit + 1)
    allowed, excessive = ParticipantUpload(ids[:limit]), ParticipantUpload(ids)
    folder = app.output_dir / Path(report_name).stem
    _upload_boundary_file(app, allowed, folder, 'at_limit', reset=True)
    verify_upload_preview(app, allowed)
    submit_participant_upload(app)
    verify_uploaded_participant_count(app, limit)
    applied_url = app.page.url
    _upload_boundary_file(app, excessive, folder, 'over_limit')
    failures_before = len(app.failures)
    verify_upload_limit_rejected(app, limit, folder)
    if len(app.failures) == failures_before:
        assert app.page.url == applied_url, 'Rejected upload changed the applied participant set'
        verify_uploaded_participant_count(app, limit)
        app.results.append({'check': 'Text-file participant limit', 'status': 'PASSED', 'detail': f'{limit} accepted; {limit + 1} rejected'})


# ---------------------------------------------------------------------------
# Dismissal and removal controls
# ---------------------------------------------------------------------------

def close_participant_upload(app):
    """Close using the X icon without submitting draft edits."""
    dialog = _dialog(app)
    _control(app, 'Close', dialog).click()
    expect(dialog).not_to_be_visible()


def read_upload_baseline_count(app):
    """Record the original Explore total before applying a participant set."""
    expect(_control(app, 'InputSet')).not_to_be_visible()
    text = app.page.locator(app.repo.xpath('Statbar/Participants-Count')).inner_text()
    return int(text.replace(',', '').strip())


def verify_participant_upload_empty(app):
    """Verify Clear reset both supported input controls."""
    dialog = _dialog(app)
    expect(_control(app, 'Ids', dialog)).to_have_value('')
    expect(_control(app, 'File', dialog)).to_have_value('')
    action_log.ui_action('Participant upload text and file inputs are empty.')


def remove_participant_upload(app):
    """Clear an upload-only query without accidentally removing other filters."""
    from Commons.apps.c3dc.cohort import _participant_filters
    filters = _participant_filters(parse_qs(urlparse(app.page.url).query))
    assert set(filters).issubset({'u', 'u_fc', 'u_um'}), 'Clear Query would also remove other active filters'
    expect(_control(app, 'InputSet')).to_be_visible()
    _control(app, 'RemoveSet').click()
    expect(_control(app, 'InputSet')).not_to_be_visible()


def verify_participant_upload_cleared(app, expected_count):
    """Require the original total and upload control after clearing/removing a set."""
    if not _control(app, 'Open').is_visible():
        _control(app, 'FacetPanel').click()
    expect(_control(app, 'InputSet')).not_to_be_visible(timeout=app.ui.timeout_ms)
    expect(_control(app, 'View')).not_to_be_visible()
    expect(_control(app, 'Upload')).to_be_visible()
    expect(app.page.locator(app.repo.xpath('Statbar/Participants-Count'))).to_have_text(f'{expected_count:,}', timeout=app.ui.timeout_ms)
    app.results.append({'check': 'Participant set removed', 'status': 'PASSED', 'detail': f'Original Explore total restored: {expected_count}'})
    action_log.ui_action(f'Participant set removed; original total restored: {expected_count}.')


# ---------------------------------------------------------------------------
# Unmatched participant submission (C3DC-391)
# ---------------------------------------------------------------------------

def _check_unmatched_submission(app, baseline):
    """An unmatched set must leave Explore unfiltered and expose View Set."""
    filters = parse_qs(urlparse(app.page.url).query)
    total = int(app.page.locator(app.repo.xpath('Statbar/Participants-Count')).inner_text().replace(',', ''))
    view_visible = _control(app, 'View').is_visible()
    if filters.get('u') or _control(app, 'InputSet').is_visible():
        app._fail('Unmatched participants: Submit applied a participant filter')
    if total != baseline:
        app._fail(f'Unmatched participants: Explore total changed from {baseline} to {total}')
    if not view_visible:
        app._fail('Unmatched participants: expected View Participants Set after Submit (C3DC-391)')
    return {'participant_filter': filters.get('u', []), 'participant_count': total, 'baseline_count': baseline, 'view_set_visible': view_visible}


def verify_unmatched_participants(app, count, report_name):
    """Submit generated unknown IDs; verify exact preview and unchanged Explore."""
    if count < 1:
        raise ValueError('Provide at least one unmatched participant ID')
    baseline = read_upload_baseline_count(app)
    expected = ParticipantUpload((), tuple('AUTOTEST-' + uuid4().hex.upper() for _ in range(count)))
    open_participant_upload(app)
    type_participant_ids(app, expected.submitted)
    preview = verify_upload_preview(app, expected)
    submit_participant_upload(app)
    app.ui.wait_idle()
    failures_before = len(app.failures)
    evidence = _check_unmatched_submission(app, baseline)
    evidence.update({'submitted_ids': expected.submitted, 'preview': preview})
    folder = app.output_dir / Path(report_name).stem
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'unmatched_participants.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    if len(app.failures) == failures_before:
        app.results.append({'check': 'Unmatched participants', 'status': 'PASSED', 'detail': 'Zero matches; no participant filter; Explore total unchanged; View Set available'})
