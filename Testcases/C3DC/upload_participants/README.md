# Upload Participants Set

TC01 types comma-separated participant IDs, verifies both preview lists, submits,
and compares the complete Explore participant list and stat count with the input
baseline. Valid IDs come from the current Explore page; the unmatched ID is unique
to the run. No fixed study, participant ID or expected participant total is stored.

TC02 generates a UTF-8 `.txt` file with one ID per line, including an unmatched
ID, then uploads it and performs the same preview and Explore checks. The file
is retained in this testcase's output folder as `participants.txt`.

TC03 generates a headerless UTF-8 `.csv` file with comma-separated IDs, verifies
matched/unmatched membership, and checks the submitted Explore results. The CSV
is saved under its testcase output folder as `participants.csv`.

TC04 checks the 1,500-participant limit using **text-file upload only**.
A single read-only request based on Explore's participant lookup supplies source
IDs. It uploads `at_limit.txt` (1,500 IDs), verifies the preview and stat count,
then uploads `over_limit.txt` (1,501 IDs) and requires rejection. No results-table
pagination is used. Files and failure evidence are retained under TC04's output
folder.

TC05 submits an initial set, reopens and verifies its retained input and match
lists, then replaces it with a disjoint set captured before filtering. It checks
exact Explore membership after each submission and reopens the replacement set
to verify the updated input is retained.

TC06 clears an unsubmitted draft and verifies empty inputs, then applies a set
and verifies Cancel and X preserve its exact membership after unsaved edits.
Finally it uses Clear Query to remove the uploaded set (the sole active filter)
and checks that the original Explore
total and Upload Participants Set control return.

TC07 submits generated unknown IDs and verifies every ID appears under Unmatched
with zero matches. Following [C3DC-391](https://tracker.nci.nih.gov/browse/C3DC-391),
Submit must leave Explore unfiltered, preserve its participant total, and change
the upload button to View Participants Set. Evidence is saved as
`unmatched_participants.json`. Blank/empty input and unsupported-format validation
are excluded because their expected feedback is not specified in this requirement.

TC08 repeats dynamically selected valid IDs with surrounding spaces, line breaks
and a trailing comma. It checks that the preview contains only the unique IDs,
then submits and verifies exact Explore membership and its participant count.
ID case is preserved; case-insensitive matching is not assumed.

```bash
pytest Testcases/C3DC/upload_participants/TC01_C3DC_Verify_Upload_Participants_TypedIDs.xlsx --env qa --headed --slowmo 500
```

Reusable functions live in `Commons/apps/c3dc/upload_participants.py`; locators
live in `ObjectRepository/C3DC/upload_participants.yaml`. The public functions
accept an app plus explicit IDs, file paths or expected sets:

```python
from Commons.apps.c3dc import upload_participants as upload

expected = upload.ParticipantUpload(tuple(valid_ids), tuple(unknown_ids))
upload.open_participant_upload(app)
upload.type_participant_ids(app, expected.submitted)
upload.verify_upload_preview(app, expected)
upload.submit_participant_upload(app)
upload.verify_uploaded_participants(app, expected.matched, report_name)
```

`attach_participant_file(app, path)` selects a file; `clear_participant_upload`
and `cancel_participant_upload` handle draft controls. Clear closes the dialog;
call `open_participant_upload` to continue with a fresh upload. File uploads are covered
by TC02 (text) and TC03 (CSV). Helpers do not navigate automatically, so callers can
reuse them after cohort or Analyzer workflows return to Explore.

TC01 uses uppercase source-style participant IDs from the current page. CPI IDs
shown in Explore may have different upload matching semantics; CPI mapping is
not asserted by this happy-path case. Exact source and result membership are
saved in `OutputFiles/C3DC/<ENV>/<testcase>/participant_upload.json`.

QA text-file check: 1,500 IDs were accepted, but 1,501 were also accepted without
limit validation. TC04 currently fails that rejection check (about 22 seconds).

TC07 QA: exact unmatched IDs, zero matches, no participant filter and unchanged
Explore total passed. The button remains Upload Participants Set after Submit,
so the View Participants Set expectation from C3DC-391 currently fails.
