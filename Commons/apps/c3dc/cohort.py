"""Create cohorts through the UI and read their shared management popup.

The popup helpers also work from Cohort Analyzer. Expected participants come
from the filtered UI, so this workflow does not depend on a separate DB snapshot.
"""
from dataclasses import dataclass
import re

from playwright.sync_api import expect

from Commons import action_log


@dataclass(frozen=True)
class CohortCreation:
    """The UI baseline recorded immediately before creating a cohort."""

    previous_cohort_count: int
    participants: tuple[tuple[str, str], ...]  # (participant ID, study ID)


@dataclass(frozen=True)
class CohortDetails:
    """Visible information for the selected cohort, reusable in Analyzer tests."""

    name: str
    participant_count: int
    participants: tuple[tuple[str, str], ...]


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
    return CohortDetails(name, participant_count, tuple(tuple(row) for row in participants))


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
    participants = read_filtered_participants(app)
    view_all = app.ui.visible(app.repo.xpath("Cohort/ViewAll"))
    before = int(re.search(r"\((\d+)\)", view_all.inner_text()).group(1))
    if before >= 20:
        raise AssertionError("Cannot create a cohort: the UI already contains the maximum 20 cohorts")
    app._cohort_creation = CohortCreation(before, participants)
    app.ui.click(app.repo.xpath("Cohort/CreateNew"), repo_key="Cohort/CreateNew")
    app.ui.click(app.repo.xpath("Cohort/AllParticipants"), repo_key="Cohort/AllParticipants")
    dialog = cohort_dialog(app)
    expect(dialog.locator(f"xpath={app.repo.xpath('Cohort/Items')}")).to_have_count(before + 1)
    action_log.ui_action(f"Cohort popup opened after adding all {len(participants)} filtered participants.")


def verify_cohort_created(app):
    """Verify the new cohort and its complete membership, not just a success popup."""
    creation = getattr(app, "_cohort_creation", None)
    if creation is None:
        raise AssertionError("Create a cohort before calling verify_cohort_created")
    details = read_selected_cohort(app)
    expected = set(creation.participants)
    actual = set(details.participants)
    checks = {
        "new cohort name": bool(re.fullmatch(r"New Cohort(?: \d+)?", details.name)),
        "participant count": details.participant_count == len(creation.participants),
        "unique participant rows": len(actual) == len(details.participants) == details.participant_count,
        "participant and study IDs": actual == expected,
    }
    for check, passed in checks.items():
        if not passed:
            app._fail(
                f"Cohort {details.name!r}: {check} failed. Expected {len(expected)} participants; "
                f"popup shows {details.participant_count}. Missing IDs: {sorted(expected - actual)[:10]}; "
                f"unexpected IDs: {sorted(actual - expected)[:10]}"
            )
        else:
            app.results.append({"check": f"Cohort {check}", "status": "PASSED", "detail": details.name})
    if all(checks.values()):
        action_log.ui_action(f"Cohort {details.name!r} created with all {details.participant_count} filtered participants.")
    return details
