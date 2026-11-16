"""Create cohorts through the UI and read their shared management popup.

The popup helpers also work from Cohort Analyzer. All-participant creation uses
the filtered stat count without reading or paginating the results table.
"""
from dataclasses import dataclass
import csv
import json
from pathlib import Path
import re

from playwright.sync_api import expect

from Commons import action_log


# ---------------------------------------------------------------------------
# Cohort snapshots and downloaded files
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CohortCreation:
    """The UI baseline recorded immediately before creating a cohort."""

    previous_cohort_count: int
    participant_count: int
    study_id: str | None = None
    # Optional exact membership for workflows that already know the selected IDs.
    participants: tuple[tuple[str, str], ...] | None = None


@dataclass(frozen=True)
class CohortDetails:
    """Visible information for the selected cohort, reusable in Analyzer tests."""

    name: str
    participant_count: int
    participants: tuple[tuple[str, str], ...]
    description: str = ""


@dataclass(frozen=True)
class CohortDuplication:
    """Source popup data recorded before clicking Duplicate."""

    source: CohortDetails
    item_ids: tuple[str, ...]


@dataclass(frozen=True)
class CohortEdit:
    """Requested metadata and original membership, retained across page reloads."""

    original: CohortDetails
    name: str
    description: str
    cohort_count: int


@dataclass(frozen=True)
class CohortManifest:
    """The selected cohort snapshot paired with this run's downloaded CSV."""

    source: CohortDetails
    path: Path


@dataclass(frozen=True)
class CohortMetadata:
    """The cohort snapshot and JSON file retained for metadata verification."""

    source: CohortDetails
    path: Path


# ---------------------------------------------------------------------------
# Shared popup navigation and cohort details
# ---------------------------------------------------------------------------

def cohort_dialog(app):
    """Wait for the cohort popup and return its scope, excluding the page behind it."""
    dialog = app.ui.visible(app.repo.xpath("Cohort/Dialog"))
    expect(dialog).to_be_visible(timeout=app.ui.timeout_ms)
    return dialog


def open_cohorts(app):
    """Open the existing-cohorts popup without changing any cohort."""
    app.click("Cohort/ViewAll")
    return cohort_dialog(app)


def select_cohort(app, name: str):
    """Select a cohort by its displayed name, including names containing quotes."""
    dialog = cohort_dialog(app)
    item = dialog.get_by_role("option", name=f"Cohort: {name}", exact=True)
    item.click()
    expect(item).to_have_attribute("aria-selected", "true")
    action_log.ui_action(f"Selected cohort: {name}.")


def close_cohorts(app):
    """Close an unchanged popup. Unsaved edits must be handled by their own workflow."""
    dialog = cohort_dialog(app)
    dialog.locator(f"xpath={app.repo.xpath('Cohort/Close')}").click()
    expect(dialog).not_to_be_visible()


def read_selected_cohort(app) -> CohortDetails:
    """Read the selected name, total and all rows, including rows below the scrollbar."""
    dialog = cohort_dialog(app)
    selected = dialog.locator(f"xpath={app.repo.xpath('Cohort/SelectedItem')}")
    expect(selected).to_have_count(1)
    name = selected.get_attribute("aria-label").removeprefix("Cohort: ")
    count = dialog.locator(f"xpath={app.repo.xpath('Cohort/ParticipantCount')}")
    expect(count).to_have_text(re.compile(r"PARTICIPANTS IDs\s*\([\d,]+\)"))
    participant_count = int(re.search(r"\(([\d,]+)\)", count.inner_text()).group(1).replace(",", ""))
    rows = dialog.locator(f"xpath={app.repo.xpath('Cohort/ParticipantRows')}")
    # Rows are all in the DOM even when the popup's scroll area only shows eight.
    expect(rows).to_have_count(participant_count, timeout=app.ui.timeout_ms)
    participants = rows.evaluate_all(
        "rows => rows.map(row => Array.from(row.children).slice(0, 2)"
        ".map(cell => cell.innerText.trim()))"
    )
    description = dialog.locator(f"xpath={app.repo.xpath('Cohort/Description')}").input_value()
    return CohortDetails(name, participant_count, tuple(tuple(row) for row in participants), description)


# ---------------------------------------------------------------------------
# Participant selection and cohort creation
# ---------------------------------------------------------------------------

def read_filtered_participants(app) -> tuple[tuple[str, str], ...]:
    """Read every filtered result page, rather than only the first 50 participants."""
    app.open_tab("Participants")
    app._wait_explore_results_ready()
    count_text = app.ui.text(app.repo.xpath("Statbar/Participants-Count"))
    expected_count = int(count_text.replace(",", "").strip())
    if expected_count == 0:
        raise AssertionError("Cannot create an all-participants cohort: the filters returned no participants")

    container = app.ui.visible(app.repo.xpath("ResultTabs/Participants-Tbl"))
    headers = [text.strip() for text in container.locator("thead th").all_inner_texts()]
    participant_column = headers.index("Participant ID") + 1
    first_participant = container.locator(f"tbody tr:first-child td:nth-child({participant_column})")
    previous_button = container.get_by_role("button", name="Previous page", exact=True).first
    # Rewind so this helper is safe after another test step paginates the table.
    for _ in range(app.MAX_PAGES):
        if not previous_button.is_enabled():
            break
        previous_id = first_participant.inner_text()
        previous_button.click()
        expect(first_participant).not_to_have_text(previous_id, timeout=app.ui.timeout_ms)
    else:
        raise AssertionError("Could not return to the first Participants page")

    participants = []
    for _ in range(app.MAX_PAGES):
        # Resolve columns by header, so optional CPI columns do not shift IDs.
        page_rows = container.evaluate("""root => {
            const table = root.querySelector('table');
            const headers = Array.from(table.querySelectorAll('thead th'))
                .map(cell => cell.innerText.trim());
            const participantColumn = headers.indexOf('Participant ID');
            const studyColumn = headers.indexOf('Study ID');
            if (participantColumn < 0 || studyColumn < 0)
                throw new Error('Participants table is missing ID columns');
            return Array.from(table.querySelectorAll('tbody tr')).map(row => {
                const cells = row.querySelectorAll('td');
                return [cells[participantColumn].innerText.trim(), cells[studyColumn].innerText.trim()];
            });
        }""")
        participants.extend(tuple(row) for row in page_rows)
        next_button = container.get_by_role("button", name="Next page", exact=True).first
        if not next_button.is_enabled():
            break
        previous_id = page_rows[0][0]
        next_button.click()
        # The page counter can advance before the async participant rows arrive.
        # Wait for the first actual ID to change before reading the next page.
        expect(first_participant).not_to_have_text(previous_id, timeout=app.ui.timeout_ms)
    else:
        raise AssertionError(f"Participants pagination exceeded {app.MAX_PAGES} pages")

    if len(participants) != expected_count or len(set(participants)) != expected_count:
        raise AssertionError(
            f"Filtered table returned {len(participants)} rows / {len(set(participants))} unique participants; "
            f"the stat bar shows {expected_count}"
        )
    return tuple(participants)


def create_cohort_from_all_participants(app):
    """Choose Create New Cohort > All Participants and wait for the resulting popup."""
    # Keep the baseline on this app instance, not in global state or localStorage.
    app._cohort_creation = None
    count_text = app.ui.stable_text(
        app.repo.xpath("Statbar/Participants-Count"), settle_s=0.75,
        timeout_s=30, label="cohort_participants_stat",
    )
    participant_count = int(count_text.replace(",", "").strip())
    if participant_count == 0:
        raise AssertionError("Cannot create an all-participants cohort: the filters returned no participants")
    _create_cohort(app, "Cohort/AllParticipants", participant_count)


def _create_cohort(app, option_key, participant_count, participants=None):
    """Create via either menu option, retaining the appropriate verification baseline."""
    app._cohort_creation = None
    view_all = app.ui.visible(app.repo.xpath("Cohort/ViewAll"))
    before = int(re.search(r"\((\d+)\)", view_all.inner_text()).group(1))
    if before >= 20:
        raise AssertionError("Cannot create a cohort: the UI already contains the maximum 20 cohorts")
    app._cohort_creation = CohortCreation(
        before, participant_count, getattr(app, "_active_study_accession", None), participants,
    )
    app.ui.click(app.repo.xpath("Cohort/CreateNew"), repo_key="Cohort/CreateNew")
    app.ui.click(app.repo.xpath(option_key), repo_key=option_key)
    dialog = cohort_dialog(app)
    expect(dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}")).to_have_count(before + 1)
    action_log.ui_action(f"Cohort popup opened after adding {participant_count} participants via {option_key}.")


def _selected_option_is_enabled(option):
    """The live menu is a plain li: its disabled state has no aria/disabled attribute.

    Production renders cursor:default without selections and cursor:pointer
    when enabled. The disabled check also clicks it to verify no cohort is made.
    """
    return option.evaluate("el => getComputedStyle(el).cursor === 'pointer' && el.getAttribute('aria-disabled') !== 'true'")


def verify_selected_participants_option(app, state):
    """Open Create New Cohort and verify the Selected Participants menu state."""
    if state not in ("enabled", "disabled"):
        raise ValueError("Selected Participants state must be 'enabled' or 'disabled'")
    before = app.ui.text(app.repo.xpath("Cohort/ViewAll"))
    app.ui.click(app.repo.xpath("Cohort/CreateNew"), repo_key="Cohort/CreateNew")
    option = app.ui.visible(app.repo.xpath("Cohort/SelectedParticipants"))
    assert _selected_option_is_enabled(option) == (state == "enabled"), f"Selected Participants should be {state}"
    if state == "disabled":
        option.click()
        expect(app.page.locator(app.repo.xpath("Cohort/Dialog"))).not_to_be_visible()
        expect(app.page.locator(app.repo.xpath("Cohort/ViewAll"))).to_have_text(before)
    # Close the custom menu only if it remains open after the disabled click.
    if option.is_visible():
        # Create New always opens this custom menu; it does not toggle closed.
        # Click neutral stat text outside the menu, leaving table selection alone.
        app.page.locator(app.repo.xpath("Statbar/Participants-Count")).click()
        expect(option).not_to_be_visible()
    app.results.append({"check": f"Selected Participants {state}", "status": "PASSED", "detail": state})
    action_log.ui_action(f"Selected Participants option is {state}.")


def _visible_participant_rows(container):
    """Read IDs from the current page by header, allowing optional CPI columns."""
    rows = container.evaluate("""root => {
        const headers = Array.from(root.querySelectorAll('thead th')).map(h => h.innerText.trim());
        const participant = headers.indexOf('Participant ID'), study = headers.indexOf('Study ID');
        if (participant < 0 || study < 0) throw new Error('Participants table is missing ID columns');
        return Array.from(root.querySelectorAll('tbody tr')).map(row => {
            const cells = row.querySelectorAll('td');
            return [cells[participant].innerText.trim(), cells[study].innerText.trim()];
        });
    }""")
    participants = tuple(tuple(row) for row in rows)
    assert participants and all(participant and study for participant, study in participants), 'No participant IDs on the current page'
    assert len(set(participants)) == len(participants), 'Duplicate participants on the current page'
    return participants


def select_participant_page(app, page_number):
    """Select a whole page, accumulating exact IDs across consecutive pages from 1."""
    if page_number < 1:
        raise ValueError("Participant page numbers start at 1")
    container = app.ui.visible(app.repo.xpath("ResultTabs/Participants-Tbl"))
    if page_number == 1:
        previous = container.locator(f"xpath={app.repo.xpath('Cohort/TopPreviousPage')}")
        expect(previous).to_be_disabled()
        app._cohort_selected_pages = {}
    else:
        pages = getattr(app, "_cohort_selected_pages", {})
        assert set(pages) == set(range(1, page_number)), 'Select participant pages consecutively from page 1'
        before = _visible_participant_rows(container)[0][0]
        headers = [h.strip() for h in container.locator('thead th').all_inner_texts()]
        first_id = container.locator(f"tbody tr:first-child td:nth-child({headers.index('Participant ID') + 1})")
        next_page = container.locator(f"xpath={app.repo.xpath('Cohort/TopNextPage')}")
        expect(next_page).to_be_enabled()
        next_page.click()
        expect(first_id).not_to_have_text(before, timeout=app.ui.timeout_ms)
    participants = _visible_participant_rows(container)
    container.locator(f"xpath={app.repo.xpath('Cohort/PageCheckbox')}").check()
    checkboxes = container.locator(f"xpath={app.repo.xpath('Cohort/RowCheckboxes')}")
    expect(checkboxes).to_have_count(len(participants))
    for checkbox in checkboxes.all():
        expect(checkbox).to_be_checked()
    app._cohort_selected_pages[page_number] = participants
    action_log.ui_action(f"Selected all {len(participants)} participants on page {page_number}.")


def create_cohort_from_selected_participants(app):
    """Create from the exact IDs accumulated by select_participant_page."""
    app._cohort_creation = None
    pages = getattr(app, "_cohort_selected_pages", {})
    participants = tuple(participant for number in sorted(pages) for participant in pages[number])
    assert participants, 'Select participant pages before creating a Selected Participants cohort'
    assert len(set(participants)) == len(participants), 'Selected pages contain overlapping participant IDs'
    _create_cohort(app, "Cohort/SelectedParticipants", len(participants), participants)


def verify_cohort_created(app):
    """Check the new cohort's name, count, unique rows and selected study."""
    creation = getattr(app, "_cohort_creation", None)
    if creation is None:
        raise AssertionError("Create a cohort before calling verify_cohort_created")
    details = read_selected_cohort(app)
    expected = set(creation.participants) if creation.participants is not None else None
    actual = set(details.participants)
    checks = {
        "new cohort name": bool(re.fullmatch(r"New Cohort(?: \d+)?", details.name)),
        "participant count": details.participant_count == creation.participant_count,
        "unique participant rows": len(actual) == len(details.participants) == details.participant_count,
    }
    if creation.study_id:
        checks["selected study IDs"] = all(study == creation.study_id for _, study in details.participants)
    if expected is not None:
        checks["participant and study IDs"] = actual == expected
    for check, passed in checks.items():
        if not passed:
            app._fail(
                f"Cohort {details.name!r}: {check} failed. Expected {creation.participant_count} participants; "
                f"popup shows {details.participant_count}."
                + (f" Missing IDs: {sorted(expected - actual)[:10]}; unexpected IDs: {sorted(actual - expected)[:10]}"
                   if expected is not None else "")
            )
        else:
            app.results.append({"check": f"Cohort {check}", "status": "PASSED", "detail": details.name})
    if all(checks.values()):
        action_log.ui_action(f"Cohort {details.name!r} created with the expected {details.participant_count} participants.")
    return details


# ---------------------------------------------------------------------------
# Cohort duplication and creation limit
# ---------------------------------------------------------------------------

def duplicate_selected_cohort(app):
    """Duplicate the selected popup cohort without touching the results table."""
    app._cohort_duplication = None
    dialog = cohort_dialog(app)
    items = dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}")
    item_ids = tuple(items.evaluate_all("items => items.map(item => item.id)"))
    if len(item_ids) >= 20:
        raise AssertionError("Cannot duplicate a cohort: the UI already contains the maximum 20 cohorts")
    source = read_selected_cohort(app)
    app._cohort_duplication = CohortDuplication(source, item_ids)
    duplicate = dialog.locator(f"xpath={app.repo.xpath('Cohort/DuplicateSelected')}")
    expect(duplicate).to_have_count(1)
    expect(duplicate).to_be_enabled()
    duplicate.click()
    expect(items).to_have_count(len(item_ids) + 1)
    selected = dialog.locator(f"xpath={app.repo.xpath('Cohort/SelectedItem')}")
    expect(selected).not_to_have_attribute("aria-label", f"Cohort: {source.name}")
    action_log.ui_action(f"Duplicated cohort {source.name!r} from View All Cohorts.")


def _duplicate_data_checks(source, duplicate):
    """Compare popup data without changing the selected cohort."""
    return {
        "participant count": duplicate.participant_count == source.participant_count,
        "unique participant rows": len(set(duplicate.participants)) == len(duplicate.participants) == duplicate.participant_count,
        "participant and study IDs": set(duplicate.participants) == set(source.participants),
        "description": duplicate.description == source.description,
    }


def verify_duplicate_cohort_created(app):
    """Compare the complete copy with its source, then confirm the source is unchanged."""
    baseline = getattr(app, "_cohort_duplication", None)
    if baseline is None:
        raise AssertionError("Duplicate a cohort before calling verify_duplicate_cohort_created")
    duplicate = read_selected_cohort(app)
    source = baseline.source
    dialog = cohort_dialog(app)
    ids = dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}").evaluate_all("items => items.map(item => item.id)")
    selected_id = dialog.locator(f"xpath={app.repo.xpath('Cohort/SelectedItem')}").get_attribute("id")
    added = set(ids) - set(baseline.item_ids)
    # The first copy is '(Copy)'; subsequent copies can have a numeric suffix.
    base_name = re.sub(r" \(Copy(?: \d+)?\)$", "", source.name)
    checks = {
        "one additional cohort": len(ids) == len(baseline.item_ids) + 1 and len(added) == 1,
        "existing cohorts retained": set(baseline.item_ids).issubset(ids),
        "duplicate selected": selected_id in added,
        "copy name": bool(re.fullmatch(re.escape(base_name) + r" \(Copy(?: [1-9]\d*)?\)", duplicate.name)),
        **_duplicate_data_checks(source, duplicate),
    }
    select_cohort(app, source.name)
    original = read_selected_cohort(app)
    checks["source unchanged"] = (
        original.name == source.name and original.description == source.description
        and original.participant_count == source.participant_count
        and set(original.participants) == set(source.participants)
        and len(original.participants) == len(source.participants)
    )
    select_cohort(app, duplicate.name)
    for check, passed in checks.items():
        if passed:
            app.results.append({"check": f"Duplicate cohort {check}", "status": "PASSED", "detail": duplicate.name})
        else:
            app._fail(f"Duplicate cohort {duplicate.name!r}: {check} failed against source {source.name!r}")
    if all(checks.values()):
        action_log.ui_action(f"Duplicate {duplicate.name!r} preserves all {source.participant_count} participants; source unchanged.")
    return duplicate


def duplicate_cohort_repeatedly(app, count):
    """Perform a requested number of real Duplicate clicks, checking every copy."""
    if count < 1:
        raise ValueError("Duplicate count must be at least 1")
    app._cohort_limit_source = None
    dialog = cohort_dialog(app)
    before = dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}").count()
    if before + count > 20:
        raise AssertionError(f"Cannot duplicate {count} times from {before} cohorts: the maximum is 20")
    app._cohort_limit_source = read_selected_cohort(app)
    for number in range(1, count + 1):
        duplicate_selected_cohort(app)
        # Keep the newly-created copy selected for the next Duplicate click.
        # Compare each copy to the original snapshot without switching cohorts.
        copy = read_selected_cohort(app)
        checks = _duplicate_data_checks(app._cohort_limit_source, copy)
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise AssertionError(f"Duplicate {number} of {count} failed verification: {', '.join(failed)}")
        app.results.append({"check": f"Duplicate {number} data", "status": "PASSED", "detail": copy.name})
        action_log.ui_action(f"Verified duplicate {number}/{count}; cohort count is {before + number}.")


def verify_duplicate_cohort_limit(app):
    """Require 20 cohorts and inspect actual disabled controls, not helper guards."""
    dialog = cohort_dialog(app)
    items = dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}")
    expect(items).to_have_count(20)
    ids = items.evaluate_all("items => items.map(item => item.id)")
    assert len(set(ids)) == 20, "The limit must contain 20 distinct cohorts"
    buttons = dialog.locator(f"xpath={app.repo.xpath('Cohort/DuplicateButtons')}")
    expect(buttons).to_have_count(20)
    for button in buttons.all():
        expect(button).to_be_disabled()
    selected = dialog.locator(f"xpath={app.repo.xpath('Cohort/DuplicateSelected')}")
    expect(selected).to_have_count(1)
    expect(selected).to_be_disabled()
    source = getattr(app, "_cohort_limit_source", None)
    if source is not None:
        select_cohort(app, source.name)
        original = read_selected_cohort(app)
        assert (
            original.name == source.name and original.description == source.description
            and original.participant_count == source.participant_count
            and len(original.participants) == len(source.participants)
            and set(original.participants) == set(source.participants)
        ), "Original cohort changed while creating duplicates"
    expect(items).to_have_count(20)
    app.results.append({"check": "Duplicate cohort creation limit", "status": "PASSED", "detail": "20 cohorts; all Duplicate buttons disabled"})
    action_log.ui_action("Cohort limit verified: 20 cohorts and all Duplicate buttons disabled.")


# ---------------------------------------------------------------------------
# Removal confirmations, cancellation, and deletion
# ---------------------------------------------------------------------------

def verify_cohort_removal_confirmation(app, target, expected_message):
    """Verify Cancel preserves cohorts, then Confirm removes the intended cohort(s).

    Targets distinguish the table-header trash, selected list entry, and list
    header. Individual blue participant-row trash icons are a different workflow.
    Expected copy comes from the testcase rather than from a UI-derived baseline.
    """
    controls = {
        "table": "Cohort/DeleteFromTable",
        "cohort": "Cohort/DeleteSelected",
        "all": "Cohort/DeleteAll",
    }
    if target not in controls:
        raise ValueError("Removal target must be table, cohort, or all")
    if not expected_message.strip():
        raise ValueError("An expected removal confirmation message is required")
    dialog = cohort_dialog(app)
    items = dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}")
    before_ids = items.evaluate_all("items => items.map(item => item.id)")
    before = read_selected_cohort(app)
    selected_id = dialog.locator(f"xpath={app.repo.xpath('Cohort/SelectedItem')}").get_attribute("id")
    dialog.locator(f"xpath={app.repo.xpath(controls[target])}").click()
    confirmation = app.page.locator(app.repo.xpath("Cohort/RemovalConfirmation"))
    expect(confirmation).to_be_visible(timeout=app.ui.timeout_ms)
    cancel = confirmation.locator(f"xpath={app.repo.xpath('Cohort/CancelRemoval')}")
    try:
        message = confirmation.locator(f"xpath={app.repo.xpath('Cohort/RemovalMessage')}")
        # Lines are separate block spans. Compare rendered text so line breaks
        # become whitespace, while still requiring the entire expected message.
        expect(message).to_have_text(expected_message, use_inner_text=True)
        confirm = confirmation.locator(f"xpath={app.repo.xpath('Cohort/ConfirmRemoval')}")
        for button in (confirm, cancel):
            expect(button).to_be_visible()
            expect(button).to_be_enabled()
    finally:
        # A changed warning must fail safely before any deletion is attempted.
        cancel.click()
        expect(confirmation).not_to_be_visible()
    assert items.evaluate_all("items => items.map(item => item.id)") == before_ids, "Cancelling removal changed the cohort list"
    assert read_selected_cohort(app) == before, "Cancelling removal changed the selected cohort"
    action_log.ui_action(f"Verified {target} removal message and Cancel; cohorts unchanged.")

    # Reopen the same control and verify the warning again before confirming.
    dialog.locator(f"xpath={app.repo.xpath(controls[target])}").click()
    expect(confirmation).to_be_visible(timeout=app.ui.timeout_ms)
    try:
        expect(message).to_have_text(expected_message, use_inner_text=True)
        expect(confirm).to_be_visible()
        expect(confirm).to_be_enabled()
    except AssertionError:
        cancel.click()
        raise
    confirm.click()
    expect(confirmation).not_to_be_visible()
    expected_ids = [] if target == "all" else [item_id for item_id in before_ids if item_id != selected_id]
    expect(items).to_have_count(len(expected_ids))
    assert items.evaluate_all("items => items.map(item => item.id)") == expected_ids, "Confirm removed the wrong cohort(s)"
    view_all = app.page.locator(app.repo.xpath("Cohort/ViewAll"))
    expect(view_all).to_have_text(f"VIEW ALL COHORTS({len(expected_ids)})")

    # Reload and reopen so disappearing rows alone cannot count as persisted deletion.
    if dialog.is_visible():
        close_cohorts(app)
    app.page.reload(wait_until="domcontentloaded")
    app.ui.wait_idle()
    for key in app.BANNER_KEYS:
        if app.page.locator(app.repo.xpath(key)).is_visible():
            app.accept_banner()
            break
    expect(view_all).to_have_text(f"VIEW ALL COHORTS({len(expected_ids)})")
    if expected_ids:
        dialog = open_cohorts(app)
        items = dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}")
        expect(items).to_have_count(len(expected_ids))
        assert items.evaluate_all("items => items.map(item => item.id)") == expected_ids, "Deleted cohort(s) returned after reload"
    app.results.append({"check": f"Cohort removal confirmation ({target})", "status": "PASSED", "detail": f"{expected_message} Cancel preserved cohorts; Confirm removed the intended cohort(s), including after reload."})
    action_log.ui_action(f"Confirmed {target} removal; {len(expected_ids)} cohorts remain after reload.")


# ---------------------------------------------------------------------------
# Manifest CSV download and participant verification
# ---------------------------------------------------------------------------

def download_cohort_manifest(app, report_name="cohort_manifest"):
    """Select the current cohort and capture its Manifest CSV in OutputFiles.

    Playwright's download is temporary; save_as retains it directly in the
    application's environment-specific output folder before the browser closes.
    """
    app._cohort_manifest = None
    source = read_selected_cohort(app)
    path = _download_cohort_file(app, source, 'Cohort/ManifestCSV', '.csv', report_name)
    app._cohort_manifest = CohortManifest(source, path)
    return path


def _download_cohort_file(app, source, format_key, extension, report_name):
    """Shared browser download and output retention for CSV and JSON exports."""
    select_cohort(app, source.name)
    dialog = cohort_dialog(app)
    dialog.locator(f"xpath={app.repo.xpath('Cohort/DownloadSelected')}").click()
    with app.page.expect_download(timeout=30000) as event:
        dialog.locator(f"xpath={app.repo.xpath(format_key)}").click()
    download = event.value
    filename = Path(download.suggested_filename).name
    assert filename.lower().endswith(extension), f"Expected a {extension} cohort export, got {filename!r}"
    folder = app.output_dir / Path(report_name).stem
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / filename
    download.save_as(path)
    assert path.is_file() and path.stat().st_size > 0, "Downloaded cohort export is missing or empty"
    action_log.ui_action(f"Saved selected cohort export: {path}")
    return path


def _read_manifest_participants(path):
    """Read real CSV quoting/BOMs and reject rows without both identifying IDs."""
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream, strict=True)
        required = {'Participant ID', 'Study ID'}
        assert required.issubset(reader.fieldnames or []), "Manifest requires Participant ID and Study ID columns"
        participants = []
        for row in reader:
            assert None not in row, f"Malformed manifest row {reader.line_num}: extra columns"
            participant = (row.get('Participant ID') or '').strip()
            study = (row.get('Study ID') or '').strip()
            assert participant and study, f"Manifest row {reader.line_num} has a blank participant or study ID"
            participants.append((participant, study))
    assert participants, "Manifest has no participant rows"
    return participants


def _cohort_manifest_checks(source, rows):
    """Diagnosis rows repeat IDs; compare unique participant/study membership."""
    actual, expected = set(rows), set(source.participants)
    return {
        'cohort baseline complete': len(expected) == len(source.participants) == source.participant_count,
        'unique participant count': len(actual) == source.participant_count,
        'participant and study IDs': actual == expected,
    }


def verify_cohort_manifest(app):
    """Compare the saved file against the pre-download cohort, retaining evidence."""
    manifest = getattr(app, '_cohort_manifest', None)
    if manifest is None:
        raise AssertionError("Download a cohort manifest before verifying it")
    rows = _read_manifest_participants(manifest.path)
    checks = _cohort_manifest_checks(manifest.source, rows)
    actual, expected = set(rows), set(manifest.source.participants)
    evidence = {
        'cohort': manifest.source.name, 'manifest': manifest.path.name,
        'csv_rows': len(rows), 'expected_participants': manifest.source.participant_count,
        'actual_unique_participants': len(actual), 'checks': checks,
        'missing_participants': sorted(expected - actual),
        'unexpected_participants': sorted(actual - expected),
        'expected_participant_study_ids': sorted(expected),
        'actual_participant_study_ids': sorted(actual),
    }
    manifest.path.with_suffix('.verification.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    for check, passed in checks.items():
        if passed:
            app.results.append({'check': f'Cohort manifest {check}', 'status': 'PASSED', 'detail': str(manifest.path)})
        else:
            app._fail(f"Cohort manifest {check} failed: expected {manifest.source.participant_count}, actual {len(actual)} unique participants; missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}")
    if all(checks.values()):
        action_log.ui_action(f"Manifest verified: {len(rows)} diagnosis rows, all {len(actual)} cohort participant/study IDs match.")


# ---------------------------------------------------------------------------
# Metadata JSON download and hierarchy verification
# ---------------------------------------------------------------------------

def download_cohort_metadata(app, report_name="cohort_metadata"):
    """Download the selected cohort's Metadata JSON using the shared export flow."""
    app._cohort_metadata = None
    source = read_selected_cohort(app)
    path = _download_cohort_file(app, source, 'Cohort/MetadataJSON', '.json', report_name)
    app._cohort_metadata = CohortMetadata(source, path)
    return path


def _metadata_participant_pairs(data, cohort_name):
    """Validate the exported hierarchy and resolve each participant's study ID.

    JSON participants sit under study/consent_groups, rather than flat rows.
    Check their GUID links so the right IDs under the wrong parent cannot pass.
    """
    assert isinstance(data, dict) and set(data) == {cohort_name}, "Metadata must contain only the selected cohort name"
    studies = data[cohort_name]
    assert isinstance(studies, list) and studies, "Metadata cohort must contain study objects"
    pairs, study_ids = [], []
    for study in studies:
        assert isinstance(study, dict), "Metadata study must be an object"
        study_id = study.get('study_id')
        assert isinstance(study_id, str) and study_id.strip(), "Metadata study_id is missing"
        assert study.get('dbgap_accession') == study_id, "Metadata study_id and dbgap_accession differ"
        assert isinstance(study.get('guid'), str) and study['guid'], "Metadata study GUID is missing"
        study_ids.append(study_id)
        groups = study.get('consent_groups')
        assert isinstance(groups, list), "Metadata consent_groups must be an array"
        for group in groups:
            assert isinstance(group, dict) and group.get('guid'), "Metadata consent group GUID is missing"
            participants = group.get('participants')
            assert isinstance(participants, list), "Metadata participants must be an array"
            for participant in participants:
                assert isinstance(participant, dict), "Metadata participant must be an object"
                participant_id = participant.get('participant_id')
                assert isinstance(participant_id, str) and participant_id.strip(), "Metadata participant_id is missing"
                assert participant.get('study_guid') == study['guid'], "Metadata participant links to the wrong study"
                assert participant.get('consent_group_guid') == group['guid'], "Metadata participant links to the wrong consent group"
                pairs.append((participant_id, study_id))
    assert pairs, "Metadata has no participant records"
    assert len(study_ids) == len(set(study_ids)), "Metadata contains duplicate study objects"
    return pairs, set(study_ids)


def verify_cohort_metadata(app):
    """Parse saved JSON and compare cohort name, hierarchy, count and membership."""
    metadata = getattr(app, '_cohort_metadata', None)
    if metadata is None:
        raise AssertionError("Download cohort metadata before verifying it")
    data = json.loads(metadata.path.read_text(encoding='utf-8-sig'))
    rows, study_ids = _metadata_participant_pairs(data, metadata.source.name)
    checks = _cohort_manifest_checks(metadata.source, rows)
    checks['unique participant records'] = len(rows) == len(set(rows))
    checks['study IDs'] = study_ids == {study_id for _, study_id in metadata.source.participants}
    actual, expected = set(rows), set(metadata.source.participants)
    evidence = {
        'cohort': metadata.source.name, 'metadata': metadata.path.name,
        'cohort name and hierarchy': 'PASSED', 'participant_records': len(rows),
        'expected_participants': metadata.source.participant_count,
        'actual_unique_participants': len(actual), 'checks': checks,
        'missing_participants': sorted(expected - actual),
        'unexpected_participants': sorted(actual - expected),
        'expected_participant_study_ids': sorted(expected),
        'actual_participant_study_ids': sorted(actual),
    }
    metadata.path.with_suffix('.verification.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    app.results.append({'check': 'Cohort metadata name and hierarchy', 'status': 'PASSED', 'detail': str(metadata.path)})
    for check, passed in checks.items():
        if passed:
            app.results.append({'check': f'Cohort metadata {check}', 'status': 'PASSED', 'detail': str(metadata.path)})
        else:
            app._fail(f"Cohort metadata {check} failed: expected {metadata.source.participant_count}, actual {len(actual)} unique participants; missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}")
    if all(checks.values()):
        action_log.ui_action(f"Metadata JSON verified: cohort name, study/consent links, and all {len(actual)} participant/study IDs match.")


# ---------------------------------------------------------------------------
# Cohort control tooltips
# ---------------------------------------------------------------------------

def verify_cohort_tooltip(app, control, expected_text):
    """Hover a cohort control and verify the full visible tooltip text.

    Some controls initially have a title attribute. Material UI removes it on
    hover and renders an accessible tooltip instead, so inspect that live popup.
    """
    help_controls = {'CreateNewHelp', 'AddExistingHelp', 'ViewAllHelp'}
    popup_controls = {'DeleteAll', 'DeleteSelected', 'DuplicateSelected'}
    if control not in help_controls | popup_controls:
        raise ValueError(f"Unsupported cohort tooltip control: {control}")
    if not expected_text.strip():
        raise ValueError("Expected tooltip text is required")
    view_all = app.page.locator(app.repo.xpath('Cohort/ViewAll'))
    before = view_all.inner_text()
    scope = cohort_dialog(app) if control in popup_controls else app.page
    target = scope.locator(f"xpath={app.repo.xpath('Cohort/' + control)}")
    expect(target).to_have_count(1)
    expect(target).to_be_visible()
    target.hover()
    tooltip = app.page.locator(app.repo.xpath('Cohort/Tooltip'))
    expect(tooltip).to_be_visible(timeout=app.ui.timeout_ms)
    expect(tooltip).to_have_text(expected_text, use_inner_text=True)
    # Dismiss before checking another control, preventing stale-popup matches.
    # Stay inside an open modal so its overlay does not intercept the hover.
    if control in popup_controls:
        scope.locator(f"xpath={app.repo.xpath('Cohort/Close')}").hover()
    else:
        app.page.locator(app.repo.xpath('Statbar/Participants-Count')).hover()
    expect(tooltip).not_to_be_visible()
    expect(view_all).to_have_text(before)
    app.results.append({'check': f'Cohort tooltip {control}', 'status': 'PASSED', 'detail': expected_text})
    action_log.ui_action(f"Verified {control} tooltip: {expected_text}")


# ---------------------------------------------------------------------------
# Cohort name and description updates
# ---------------------------------------------------------------------------

def update_cohort_details(app, name, description):
    """Enter a new name and description, leaving Save Changes as a separate step."""
    app._cohort_edit = None
    app._cohort_edit_saved = False
    if not name.strip():
        raise ValueError("A nonempty cohort name is required")
    dialog = cohort_dialog(app)
    original = read_selected_cohort(app)
    count = dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}").count()
    dialog.locator(f"xpath={app.repo.xpath('Cohort/NameDisplay')}").click()
    name_input = dialog.locator(f"xpath={app.repo.xpath('Cohort/NameInput')}")
    expect(name_input).to_be_editable()
    name_input.fill(name)
    expect(name_input).to_have_value(name)
    # Clicking the description commits the name editor's draft on blur and
    # makes the initially-readonly description field editable.
    description_input = dialog.locator(f"xpath={app.repo.xpath('Cohort/Description')}")
    description_input.click()
    expect(description_input).to_be_editable()
    description_input.fill(description)
    expect(description_input).to_have_value(description)
    app._cohort_edit = CohortEdit(original, name, description, count)
    action_log.ui_action("Updated the cohort name and description drafts; Save Changes is next.")


def save_cohort_changes(app):
    """Save the requested metadata and require the cohort list to show the new name."""
    edit = getattr(app, "_cohort_edit", None)
    if edit is None:
        raise AssertionError("Update cohort details before calling save_cohort_changes")
    dialog = cohort_dialog(app)
    save = dialog.locator(f"xpath={app.repo.xpath('Cohort/SaveChanges')}")
    expect(save).to_be_enabled()
    save.click()
    selected = dialog.locator(f"xpath={app.repo.xpath('Cohort/SelectedItem')}")
    expect(selected).to_have_attribute("aria-label", f"Cohort: {edit.name}")
    expect(dialog.locator(f"xpath={app.repo.xpath('Cohort/Description')}")).to_have_value(edit.description)
    app._cohort_edit_saved = True
    action_log.ui_action(f"Saved cohort details for {edit.name!r}.")


def _cohort_edit_checks(edit, actual, cohort_count):
    """Compare saved metadata while guarding against unintended membership edits."""
    return {
        "saved name": actual.name == edit.name,
        "saved description": actual.description == edit.description,
        "cohort count unchanged": cohort_count == edit.cohort_count,
        "participant count unchanged": actual.participant_count == edit.original.participant_count,
        "unique participant rows": len(set(actual.participants)) == len(actual.participants) == actual.participant_count,
        "participant and study IDs unchanged": set(actual.participants) == set(edit.original.participants),
    }


def verify_cohort_details_saved(app):
    """Reload the page and reopen the popup to verify persistence, not input drafts."""
    edit = getattr(app, "_cohort_edit", None)
    if edit is None or not getattr(app, "_cohort_edit_saved", False):
        raise AssertionError("Save cohort changes before verifying persisted details")
    close_cohorts(app)
    app.page.reload(wait_until="domcontentloaded")
    app.ui.wait_idle()
    # The warning is normally remembered for the browser session, but handle
    # it if the application shows it again after reload.
    for key in app.BANNER_KEYS:
        if app.page.locator(app.repo.xpath(key)).is_visible():
            app.accept_banner()
            break
    dialog = open_cohorts(app)
    selected = dialog.locator(f"xpath={app.repo.xpath('Cohort/SelectedItem')}")
    if selected.get_attribute("aria-label") != f"Cohort: {edit.name}":
        select_cohort(app, edit.name)
    actual = read_selected_cohort(app)
    count = dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}").count()
    checks = _cohort_edit_checks(edit, actual, count)
    if edit.name != edit.original.name:
        checks["old name removed"] = dialog.get_by_role("option", name=f"Cohort: {edit.original.name}", exact=True).count() == 0
    for check, passed in checks.items():
        if passed:
            app.results.append({"check": f"Cohort update {check}", "status": "PASSED", "detail": edit.name})
        else:
            app._fail(f"Cohort update {edit.name!r}: {check} failed after reloading the page")
    if all(checks.values()):
        action_log.ui_action(f"Cohort {edit.name!r}: name and description persisted after reload; membership unchanged.")
    return actual
