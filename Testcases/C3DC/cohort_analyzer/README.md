# C3DC Cohort Analyzer

Run the complete folder on QA:

```bash
pytest Testcases/C3DC/cohort_analyzer --env qa --headed --slowmo 500
```

Each workbook is independent and ends with `assert_no_failures`. TC01 retains
its existing example-creation coverage. TC02–TC30 cover these workflows:

| Cases | Coverage |
| --- | --- |
| TC02–TC07 | Empty state, Explore cohorts, selection/limit, sorting, Cancel/Confirm removal |
| TC08–TC12 | Participant/diagnosis/treatment comparisons, Venn regions, creating a cohort from results |
| TC13–TC17 | Participant table, pagination, CSV/JSON exports, confirmed navigation to Explore |
| TC18–TC23 | Counts/percentages, chart types, add/remove, layout/reset, expanded views, survival risk table |
| TC24–TC28 | Venn, histogram, survival, combined data and combined image downloads |
| TC29–TC30 | Control tooltips and README topic navigation |

## Workbook format

The standard five parser columns are preserved. A sixth column explains the
purpose or expected result. Headers, alternating row shading, wrapped text,
frozen headings and action dropdowns make the steps readable; cell grids stay
visible. Expected notice/tooltip text and comparison choices live in the
workbook rather than in locator code.

## Reusable helpers and expected data

- Feature helpers live in `Commons/apps/c3dc/cohort_analyzer.py`; `app.py` has
  thin delegates, with C3DC-only Excel action registration.
- Locators live in `ObjectRepository/C3DC/cohort_analyzer.yaml`. Shared cohort
  creation, popup snapshots, metadata downloads and manifest parsing reuse
  `cohort.py`.
- Participant membership and counts are recorded from the original cohort popup.
  Clinical checks additionally download each cohort's separate metadata JSON.
  No study accession, participant ID, captured count or cohort name is embedded
  as expected clinical data. The three-cohort selection limit is a UI contract.
- Venn expectations use set intersections/differences. A transparent canvas
  observer records actual rendered text/coordinates while forwarding drawing
  calls unchanged; tests do not read React state or use fixed click pixels.
- Table reading visits every page and checks complete participant/study pairs.
  Clinical histogram counts count distinct participants per category. Survival
  expectations use valid source diagnosis/follow-up ages (30 days per month).
- JSON/CSV/TSV exports are parsed. PNG/PDF checks validate readable, nonblank
  image artifacts; they do not claim pixel-perfect visual or OCR verification.
- Evidence and downloads go under `OutputFiles/C3DC/<ENV>/<testcase>/`. Clinical
  comparison failures retain source baselines and expected/actual comparisons.

The cases intentionally report mismatches rather than adapting expected data to
the Analyzer's displayed values. Review the QA run report before adding them to
a required release gate, particularly clinical comparison semantics and data
availability after the recent C3DC updates.
