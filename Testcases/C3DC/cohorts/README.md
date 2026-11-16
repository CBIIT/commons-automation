# C3DC cohort testcases

`TC01_C3DC_Verify_Create_NewCohort_AllParticipants.xlsx` filters Explore Participants by study `phs002790` and race
`American Indian or Alaska Native`, then creates a cohort with All Participants.
The creation flow reads the filtered stat count and does not read or paginate
the results table. It verifies the popup count, unique rows, and study IDs.

`TC02_C3DC_Verify_Create_NewCohort_SelectedParticipants.xlsx` selects only study
`phs002790`, with no race or other filter. It checks that Selected Participants
is disabled, selects every participant on pages 1 and 2, checks that the option
is enabled, and creates the cohort. It compares all participant/study ID pairs
and the count against the exact selected rows, including selections retained
across pages. The count comes from the live pages, not a hardcoded page size.

The current custom menu has no native disabled or aria-disabled state. The test
checks its disabled/enabled cursor styling and verifies that clicking the
disabled option neither opens the cohort popup nor increases the cohort count.
Enabled creation is verified through the resulting cohort. Results-table
pagination is used only by TC02; All Participants creation never paginates.

`TC03_C3DC_Verify_Duplicate_Cohort_Creation.xlsx` creates its own source using
the same filters, closes the popup, opens View All Cohorts, and clicks the
selected cohort's Duplicate button. It checks:

- Exactly one cohort is added, all existing cohorts remain, and the copy is selected.
- The copy has the observed `(Copy)` or numbered-copy name.
- Participant count, all participant/study ID pairs, and description match the source.
- Participant rows are unique and the source remains unchanged after duplication.

`TC04_C3DC_Verify_Duplicate_Cohort_CreationLimit.xlsx` uses the same setup as
TC03, then clicks Duplicate 19 times to reach 20 cohorts. Each new copy stays
selected for the next click and its data is checked against the original snapshot.
At the boundary it requires 20 distinct cohorts and verifies
that all 20 native Duplicate buttons, including the selected cohort's button,
are disabled. It also verifies that the original source remains unchanged.
The limit check inspects actual controls; it does not use the creation helper's
20-cohort guard as evidence. Production changes each disabled button's label
to `Cohort limit reached`, which the locator explicitly includes.

`TC05_C3DC_Verify_Update_Cohort_Name_Description.xlsx` creates its own cohort,
enters a new name and a nonempty description from Params/Filter, and clicks
Save Changes. Verification closes the popup, reloads the current page, reopens
View All Cohorts, and checks both saved values. It also checks that the old name
is gone and that cohort count, participant count, and all participant/study IDs
are unchanged. The page reload distinguishes persisted changes from editor drafts.
Name/description editing, saving, and persisted-data verification are reusable
helpers in `cohort.py`; the testcase does not depend on earlier cohort cases.

`TC06_C3DC_Verify_Cohort_Removal_Confirmation.xlsx` creates its own cohort and
three duplicates. It checks the full warning text and enabled Confirm/Cancel buttons
for the red participant-table header trash, selected cohort's list trash, and
Delete All Cohorts. Each prompt is cancelled first, checking cohort IDs and selected
cohort membership remain unchanged. It then reopens the same prompt, confirms
deletion, and checks that only the intended cohort IDs disappear. The page is
reloaded after each deletion to verify persistence. Table deletion leaves three
cohorts, list deletion leaves two, and Delete All leaves zero. Expected messages live in the
testcase's Filter cells; Params selects `table`, `cohort`, or `all`. This case
covers cancellation and confirmed cohort deletion; individual blue participant-row
removal is a separate workflow.

`TC07_C3DC_Verify_Cohort_ManifestCsv_Download.xlsx` creates its own filtered cohort,
selects it in View All Cohorts, and chooses Download Selected Cohorts > Manifest
CSV. The browser download is saved directly to
`OutputFiles/C3DC/<ENV>/TC07_C3DC_Verify_Cohort_ManifestCsv_Download/` with its original
filename. Verification compares all unique participant/study ID pairs and their
count with the selected cohort's snapshot. A participant can have multiple
diagnoses, so CSV row count is recorded separately from unique participant count.
Missing, unexpected, wrong-study, or blank IDs fail verification. A companion
`.verification.json` retains the expected/actual IDs and comparison results.
Download and verification are separate reusable helpers; no database is needed.

`TC08_C3DC_Verify_Cohort_MetadataJson_Download.xlsx` uses the same independent cohort
setup and chooses Download Selected Cohorts > Metadata JSON. It retains the
original JSON under `OutputFiles/C3DC/<ENV>/TC08_C3DC_Verify_Cohort_MetadataJson_Download/`.
Verification parses the cohort-name > studies > consent_groups > participants
hierarchy, checks study/accession consistency and participant study/consent GUID
links, and compares the exact participant/study membership with the popup.
Duplicate participant records, missing/extra members, unexpected studies or
cohorts, and invalid hierarchy fail. A `.verification.json` retains comparison
evidence. This validates the cohort export structure and membership; it does not
compare every nested clinical/file field with a database or assert a cohort
description that is absent from this export format. CSV and JSON share the
browser download/save helper while retaining separate format-specific checks.

`TC09_C3DC_Verify_Cohort_Control_Tooltips.xlsx` creates its own cohort and verifies
six controls: Create New Cohort, Add Participants to Existing Cohort, View All
Cohorts, Remove All Cohorts, Remove Cohort, and Duplicate Cohort. Expected full
text lives in Filter cells; Params identifies the control in `cohort.yaml`.
All six controls render accessible tooltips on hover; Create/Add include the
4,000-participant guidance. The case checks the full rendered text, then moves
away and waits for it to disappear. View All and the popup action buttons
initially have title attributes that are replaced by rendered tooltips on hover;
the check verifies the visible popup rather than relying on those attributes.
Hover checks also require the View All cohort count to stay unchanged. No remove
or duplicate action is clicked, and no database or input workbook is required.

TC03 leaves the copy selected; TC04 selects the original for its final unchanged-data check.
Popup helpers are reusable from Cohort
Analyzer. No case needs a query workbook or database connection, and TC03
does not depend on TC01 having run. All belong to the existing C3DC regression
suite. Browser contexts isolate the cohorts created by each testcase.

Production UI inspection on 2026-11-15 confirmed the accessible Duplicate button
and the first-copy name `New Cohort (Copy)`. The fresh source has a blank description;
this case checks its preservation, without testing editing nonempty descriptions.
Use production while QA is unavailable:

```bash
python3 -m pytest Testcases/C3DC/cohorts --env prod -q
```
