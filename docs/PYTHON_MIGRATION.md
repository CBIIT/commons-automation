# Python testcase synchronization

Reference: the `commons-automation-main` repository download supplied on
November 25, 2026. Target branch: `update-py-tests`, based on `sohil-102326`.

## Execution and data

Executable workflows live in `Testcases/<APP>/**/test_*.py`. Each calls the app
adapter directly; neither the reference checkout nor Excel Steps is needed at
runtime. Input workbooks remain under `InputFiles/<APP>`, and assertions still
compare UI results with independently fetched database values.

`conftest.py` loads the HTML reporter. The Excel testcase engine, collector, and
execution-mode setting have been removed. Suite membership is defined directly
by `@pytest.mark.quickrun`, `smoke`, `regression`, and `datarelease` decorators on
the Python tests. No separate suite configuration or marker-assignment hook is
needed.

## Coverage

| Application | Python cases |
| --- | ---: |
| C3DC | 303 |
| GC | 167 |
| ICDC | 127 |
| Bento | 59 |
| INS | 41 |
| CTDC | 35 |
| PSDC | 28 |
| CCDI | 5 |
| Total | 765 |

The seven applications after C3DC contribute 462 converted cases. Their full
resolved call sequences were checked against the reference, including filters,
input filenames, action order, report names, and assertions. Cart source
navigation uses the shared `open_explore_files()` method name. Bento directory
paths use Git's canonical `Bento` casing for portability.

### C3DC coverage detail

| Workflow | Python cases |
| --- | ---: |
| Study filters and result comparisons | 203 |
| Result tabs: CSV, JSON, sorting, pagination | 24 |
| Cohort Analyzer | 30 |
| Cohorts | 14 |
| File cart | 12 |
| Participant uploads | 8 |
| Static pages and help | 6 |
| Study details | 5 |
| Study listing | 1 |
| Total | 303 |

The current study comparison covers Participants, Studies, Genetic Analysis,
Samples, Files, and Imaging Data. Clinical fields formerly displayed in separate
Diagnosis, Treatments, Treatment Responses, and Survival tabs are now represented
in the current table layout. Obsolete cases and unit checks specific to the
removed tab/binding implementation were replaced with the reference's current
test coverage and conversion checks.

The reference's helpers, object repository, and configuration were synchronized,
including shared download/sorting/pagination and app-specific implementations.
Query and data files were copied for all applications without editing workbook
content or copying secrets. C3DC input cleanup removed 36 obsolete files retained
from the original Python branch and four unreferenced files also present in the
Excel reference. The remaining 207 C3DC workbooks are unchanged.

Other applications' testcase folders now match the reference coverage. Two
unreferenced legacy input workbooks were also removed:

- `InputFiles/GC/TC04_GC_phs002677_Sex-NSD_PrimDiag_NA_FileType-TSV.xlsx`
- `InputFiles/CCDI/TC01_CCDI_StaticData.xlsx`

The PSDC PBCS study-design workbook was preserved. Its testcase's input reference
was corrected from `...Study_Pbcs_...` to the existing `...Study_PBCS_...` filename
so it also works on case-sensitive filesystems. Query contents are unchanged.

All required query/data inputs are present and match the supplied reference.
The nested CCDI publications source and all TSV data bundles were preserved.

`python_case_inventory.json` records source workbook hashes, Python paths,
input references, native pytest markers, and source step counts for all eight
applications. It replaces the earlier C3DC-only inventory. The permanent unit
checks validate coverage, query references, method signatures, filter tokens,
and final assertions without duplicating each test's implementation in JSON.
These checks do not establish live application correctness.

## Run

```bash
python3 -m pytest Testcases/unit -q
python3 -m pytest Testcases/C3DC --collect-only -q
python3 -m pytest -m "c3dc and smoke" --env qa
python3 -m pytest Testcases/C3DC/result_tabs --env qa
python3 -m pytest Testcases/C3DC --env qa -n 4
```

## Current all-application validation

The expanded unit suite passed **1,325 tests** in 69.98 seconds. All 765 application
cases execute Python directly; no testcase workbooks, Excel runner, suite YAML,
or suite loader were added to this branch. All **2,090 tests** collect: 765
application cases and 1,325 unit checks. The full all-app QA suite has not been run.

| Live selection | Result |
| --- | --- |
| GC QA2: Participants, Samples, Files CSV plus phs000720 Male study comparison | 4 passed |
| QA: CTDC Participants CSV/sorting and CMB Male study; ICDC Cases CSV; INS Programs CSV and CEDCD datasets; PSDC Studies CSV; Bento Cases sorting; CCDI About page | 5 passed, 4 failed |

The QA failures are retained with strict comparisons:

- CTDC Participants CSV and CMB study: the configured CMB snapshot contains v1
  data in `InputFiles/CTDC/CMB/2025-10-23`, while QA exposes newer cohort data and
  v6 variant archives. Saved UI/DB workbooks confirm 676 versus 148 Male
  participants and three versus four study-file rows. Both original Excel cases
  reproduce the mismatch.
- PSDC Studies CSV: PLCO has 65 cancer types and 153,786 participants in QA versus
  40 and 151,383 in the supplied reference data. The original Excel case also
  fails.
- Bento Cases sorting: Recurrence Score and Tumor Size fail to settle in numeric
  ascending/descending order for the 11-row filtered cohort. The original Excel
  workflow reproduces the same failure; the sorting expectation and app behavior
  still need review before calling this a product defect.

Representative QA successes include CTDC Participants sorting, ICDC Cases CSV,
INS Programs CSV and CEDCD dataset comparison, and CCDI About-page data. All
reference data was preserved; no expected values were replaced with UI values.

Latest validation artifacts are under `Reports/python_migration_20261125/`.


## Earlier C3DC QA validation

All 303 C3DC Python cases collect successfully. The first live QA batch passed
the `phs002790` Male study comparison across all six current tabs, Participants
CSV download, and homepage content (3 passed in 90.74 seconds).

The earlier C3DC-stage unit run passed **810 tests** in 80.64 seconds after removing four
obsolete Excel-engine registry/handler checks. This includes coverage
and input-reference checks for the migrated cases, plus both timing regressions.
That stage collected **1,474 Python tests**. Input workbook
reading and Excel comparison-report writing remain supported.

The full QA run completed in 38 minutes 48 seconds: **293 passed, 10 failed**.
All **203 study-filter cases** passed, as did the five study-detail batches
covering all 49 reference studies. Two failures were automation timing gaps;
both were fixed and their targeted live reruns passed. The latest upload batch
passed six cases and retained the two reference failures below. This leaves
eight unresolved checks; the complete 303-case suite was not rerun after the
timing fixes.

Current findings:

| Check | Observation |
| --- | --- |
| Analyzer cohort sorting (TC06) | A–Z order differs with cohorts selected; also fails in the original Excel case. |
| Analyzer diagnosis comparison (TC09) | Venn counts differ from the metadata-derived baseline; also fails in the original Excel case. |
| Analyzer chart counts/percentages (TC18) | Race `OtherFew` bucket differs from the expected aggregation; also fails in the original Excel case. |
| Analyzer layout reset (TC21) | Restored chart order differs; the drag can also fail to move a card. Both Python and original Excel cases fail. |
| Analyzer survival analysis (TC23) | Risk-table counts differ from metadata-derived expected values; also fails in the original Excel case. |
| Participants sorting | QA responds with `No mapping found for [age_at_treatment_start] in order to sort on` for ascending and descending requests. |
| Cart single-file removal | Initial parallel run read a deleted row after the total changed. Added a wait for that row to disappear; delayed-render unit regression and live rerun pass. |
| Upload update preview (TC05) | Replacement input retained the same summary counts while preview IDs were stale. Added a wait for exact matched/unmatched membership; unit regression and live rerun pass. |
| Upload limit (TC04) | The reference's 1,500-ID maximum is not visibly enforced for a 1,501-ID file; also fails in the original Excel case. |
| Unmatched-only upload (TC07) | Submit does not expose the expected View Participants Set control (C3DC-391); also fails in the original Excel case. |

The analyzer and upload observations remain baseline failures requiring
behavior/data review, not confirmed product defects. Their comparisons remain
enabled. The other five
result-tab sorting cases passed, with constant columns explicitly reported as
inconclusive where applicable. No assertions are disabled to obtain a passing run.

Local run logs are saved under `Reports/python_sync_20261125/` (gitignored).
