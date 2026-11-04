# Commons automation project guide

This repository tests seven NCI Data Commons portals using pytest and Playwright.
Excel Steps drive UI actions; separate input workbooks supply the expected Cypher,
SQL, or static page content. Fixes depend on the active filter, app schema, UI
ordering, and configured comparison limits.

Reviewed on 2026-11-04. The static inventory covers 586 testcase workbooks,
591 input workbooks, 3,856 query-bearing cells, 156 Python files, 124 YAML files
(116 locator files), 33 dataset text files, and two dataset archives. All source
workbook sheets and cells were parsed. Source Python was parsed, YAML and TSV
content read, and dataset archive payloads read. Generated reports and comparison
files were inventoried by path and size; Git internals, caches, Excel lock content,
and private environment-file content were excluded. This is a source map and
validation baseline, not a claim that every UI case or query passes.

## Finding the right file

| Task | Start here |
| --- | --- |
| Find a testcase's actual filters and steps | `Testcases/<APP>/.../TC*.xlsx`, `Steps` sheet |
| Find its input workbook | `Steps!A2`; runtime also supports a legacy row-2 column-C fallback |
| Change expected tab data | Input workbook, first sheet, `TabQuery` or legacy `query` column |
| Change expected stat counts | First nonempty `StatQuery` in the input workbook |
| Fix a UI selector or filter key | `ObjectRepository/<APP>/**/*.yaml` |
| Change app navigation or tab behavior | `Commons/apps/<app>/app.py` |
| Change an app-only Excel action | `Commons/excel_testcase/apps/<app>.py` |
| Change shared comparison or table reading | `Commons/compare.py`, `Commons/table_reader.py` |
| Change URLs, backend type, or hosts | `Config/environments.yaml` |
| Inspect secrets or local overrides | Local `.env` and shell environment; never reproduce values in documentation |
| Change row limits, pagination caps, enabled tabs | `Config/tab_setting.yaml` |
| Change suite membership | `Config/suites.yaml` |
| Inspect the actual mismatch | `OutputFiles/<APP>/<ENV>/<case>_UI.xlsx` and `_DB.xlsx` |
| Inspect the execution | `Reports/<suite>_<timestamp>.html`; `latest.html` changes with runs |

The full searchable snapshot is [repository-index.json](repository-index.json).
Its `cases` entries contain every testcase path, group, resolved input, suites,
and ordered actions with Excel row numbers. `input_workbooks` records query
tabs/rows, language heuristics, ordering, labels, relationship references, and
literal Survival selectors. `python_modules` records definitions and line numbers.
`object_repositories`, `models`, `backend_indices`, `datasets`, `archives`,
`findings`, and `files` cover the remaining source and generated-file inventory.
Query-language and literal-selector detections are static heuristics, not parsers
or proof of a live failure. `used_as_statquery` distinguishes the first stat query
from later cells that the runtime ignores.

For example, filter the index without reading its entire contents:

```bash
python3 - <<'PY'
import json
from pathlib import Path
index = json.loads(Path('docs/repository-index.json').read_text())
for case in index['cases']:
    if case['app'] == 'C3DC' and 'phs002431' in case['path']:
        print(case['path'], case['input'], case['suites'])
        for step in case['steps']:
            print(' ', step)
PY
```

## Execution and comparison

1. `conftest.py` installs the Excel collector and HTML reporter, resolves CLI and
   environment settings, launches one browser per session, and makes a fresh
   browser context and app fixture per case.
2. `Commons/excel_pytest_collect.py` collects `TC*.xlsx` under registered app
   directories when `framework.test_case_source` is `excel`. Current profiles
   include studies, static pages, listings, Bento arms, and INS Programs/Datasets.
   Collection does not itself enforce `case_subdirs`; profile registration and
   the testcase path determine the app.
3. `Commons/excel_testcase/runner.py` reads the `Steps` sheet, loads the input
   workbook's basename, and dispatches actions to app-specific handlers first,
   then shared handlers. Static-data workbooks are loaded by static verification.
4. `Commons/query_reader.py` reads the first input sheet, maps `TabName` to query
   text, and takes only the first nonempty `StatQuery`. Output filename columns
   are legacy metadata; main comparison output paths come from the app and case.
5. `BaseApp` applies filters, compares stat counts, opens each requested result
   tab, reads UI data, fetches expected rows, writes highlighted output workbooks,
   and accumulates failures until `assert_no_failures()`.
6. `LazySource` delays the backend connection. `MemgraphSource` and `Neo4jSource`
   both use the `neo4j` Python Bolt driver. TSV sources merge data into SQLite.
7. `compare_tables` sorts entire rows before comparing. It tolerates specific
   formatting differences: case, whitespace, semicolon-list order, CPI badges,
   numeric text representations, and certain ICDC one-element array strings.
   Row and column count mismatches still fail. Stat counts ignore comma separators.

`verify_tab` skips tabs disabled in YAML, tabs whose associated stat is zero, and
tabs whose selected UI count is zero. A passing case may therefore contain skipped
checks. Shared `verify_tab` requires an explicit tab; `verify_all_tabs` is the
action that iterates the app's standard tabs.

`table_reader.py` handles app-specific header/cell layouts, C3DC nested tables,
table-scoped pagination controls, first-page rewind, and page-change waits. It
reads a whole DOM page before truncating collected rows to the configured limit.
Console output can show more rows than are actually compared. Sorting after
collection cannot fix a query that chose a different subset before `LIMIT`.

Study listings in C3DC and GC have separate `studies.py` flows and
`StudiesListingTab` queries. They read the listing independently of Explore's
comparison-row cap. INS Datasets likewise has a separate cards/SQL path.

## Application map

Counts are source inventory, not successful run counts. Row limits are the current
YAML values; shell or `.env` overrides can change the effective values.

| App | Excel cases | Input workbooks | Backend | YAML row cap | Case layout |
| --- | ---: | ---: | --- | ---: | --- |
| C3DC | 227 | 230 | Memgraph | 13 | 26 study folders, one listing, one static case |
| GC | 149 | 149 | Memgraph | 15 | 25 study folders, one listing, one static case |
| ICDC | 106 | 106 | Neo4j | 18 | 19 canine study folders |
| BENTO | 56 | 57 | Neo4j | 15 | Four arms with 14 cases each |
| INS | 33 | 33 | TSV and SQLite | 40 | 23 Cancer Type, six Special Topic, three Datasets, one static |
| CTDC | 14 | 15 | TSV and SQLite | 100 | AHEP0731, CMB, and one static case |
| CCDI | 1 | 1 | Neo4j configured; current case is static | 100 | Hub static pages |

All apps currently have a YAML pagination cap of 25. C3DC Treatments is disabled.
The C3DC input FilesTab rows are retained, but its adapter's standard tabs do not
include a Files tab. A query's presence alone does not mean it executes.

### C3DC

Clinical Commons Explore Participants uses Participants, Studies, Diagnosis,
Genetic Analyses, Treatments, Treatment Responses, Survival, and Samples. The
adapter normalizes tab aliases, opens tabs hidden in More, waits for stable
counts, and verifies visible participant rows belong to the selected accession
and any checked Sex at Birth values. It rechecks Participants readiness directly
before collection; a correct stat bar alone does not establish grid readiness.

The core study path is participant → consent_group → study. Race is a list.
Clinical nodes point to participants through `of_diagnosis`, `of_survival`,
`of_treatment_response`, and treatment-specific relationships. Genetic analysis
usually reaches participants through samples. Cell-line and PDX-derived samples
need additional paths in some studies.

Read `.cursor/rules/c3dc-memgraph-cypher.mdc` before query changes and
`c3dc-object-repository.mdc` before locator changes. Its primary reference is
`TC04_C3DC_phs002827_TrtmntType-Radiation.xlsx`; confirm that the specific pattern
applies to the target study and filter before copying it.

Key distinctions in those rules:

- Anchor selective cohorts early, then use `WITH DISTINCT p, s` before expanding
  to other entities. Broad participant scans with nested EXISTS can be slow on QA.
- Stat-bar Files commonly counts distinct `dcf_indexd_guid` from sample and
  participant file edges; Studies-tab counts are generally whole-study totals.
- A filter on samples, diagnosis, or treatment response can restrict records on
  that entity's own tab, while other tabs expand over the participant cohort.
- Chemotherapy-based Treatment Type filters use `chemotherapy_type` where the
  backend index does, rather than assuming `treatment_type` is equivalent.
- Top-five summaries require the appropriate record counts, tie-breaks, list
  formatting, exclusions, and Read More behavior. These vary by study.
- phs000720, phs001437, phs002430, phs002431, and phs002504 have documented
  study-specific count/path/display differences. Preserve the study context.

Some rule examples conflict or record earlier snapshots: a generic `0 AS files`
snippet coexists with later study-specific file-count rules; phs002431 examples
pin follow-up suffixes; some phs002504/phs001437 examples exclude literal records.
Treat these as historical evidence to verify, not a universal definition of
correctness. The rules also reference legacy Python tests that are now Excel.

There are two Survival query cells still using literal IDs or follow-up lists
in the current snapshot: phs002431 TC11 and phs002517 TC01.
phs002431 TC01 through TC10 use cohort-first queries with `$ui_survival_ids`
bound at runtime from currently displayed UI rows. Each retains its own study
and demographic/diagnosis predicate. Diagnosis cohorts are anchored on diagnosis
nodes and deduplicated before expanding to Survival records.

The default UI sorts by Participant ID and leaves multiple Survival rows tied.
A pure Cypher order cannot reproduce OpenSearch's unspecified tie order. For
queries explicitly opting in with this parameter, `QueryFile.bind_ui_rows`
passes only the visible Survival IDs after collection. The query still checks
study/race membership and fetches every expected field from Memgraph. Expected
clinical values are never taken from the UI. IDs are not written into query text
or saved as testcase data. Existing comparison logic and testcase UI actions
remain unchanged; no Survival ID sorting action is added.

QA and local validation matched all 13 rows and five columns of the default live
UI response. Wrong-cohort, missing, empty, and duplicate selections remain
detectable. Seven unit checks cover the binding and independent expected values.
The original QA testcase passed in 58.76 seconds with its default UI presentation
and saved Steps unchanged.

### GC

General Commons uses Data Explore with Participants, Samples, and Files, plus a
separate Studies catalog. Filters cover study metadata, demographics, diagnosis,
sample properties, sequencing, and library metadata. Many cases combine several
filters. Some input workbooks have no SamplesTab, so follow actual Steps and tab
availability rather than assuming every case verifies all three tabs.

GC has its own schema and Memgraph clusters. QA currently references the configured
gen-dev cluster and QA2 the gen-qa2 cluster; verify configuration rather than
inferring cluster identity from the UI environment name. Passwords are app- and
often environment-specific. The GC skill includes model references, but its
project-local backend-index-query reference folder is absent.

### ICDC

Canine Cases Explore compares Programs, Studies, Cases, Samples, Case Files, and
Study Files counts, with Cases, Samples, Case Files, and Study Files tables.
Studies and diagnosis/breed/disease-site/response/biobank facets use ICDC-specific
tokens. `select_study` resolves `Cases/Study` checkbox names.

ICDC can use a different Neo4j environment from its UI through `NEO4J_ENV` or
`NEO4J_ENV_ICDC`. Connectivity may require the expected VPN/host access. Seven
PRECINCT workbook SamplesTab rows have a stray backslash in later StatQuery
cells; the valid first StatQuery is what the reader uses.

### BENTO

TAILORx Explore uses `Bento` as the adapter/config name but uppercase `BENTO` for
input, testcase, and locator directories. Each arm A–D has 14 facet cases:
diagnosis, recurrence score, tumor size, chemotherapy, tumor grade, ER status,
PR status, endocrine therapy, menopause status, age, tissue type, tissue
composition, file association, and file type.

`Commons/bento_arm_filters.py` defines arm labels, distinct per-arm choices,
filenames, and age ranges. Age uses `set_age_range`, not a checkbox. Cases,
Samples, and Files queries use Neo4j. Input workbooks are flat; Steps are in arm
subfolders. Samples/files facets have their own sidebar sections.

### CTDC

Clinical Trials Explore compares six counts: Studies, Participants, Diagnoses,
Targeted Therapies, Biospecimens, and Files. Tables are Participants,
Biospecimens, Files, and Study Files. `select_study` uses `Studies/Study`.

SQL runs over merged node TSVs in SQLite, not over the C3DC Memgraph database.
`Commons/apps/ctdc/tsv_source.py` maps nodes to `df_*` tables, including specimen
→ `df_biospecimen`. Snapshots are merged oldest to newest by node-specific keys.
Current release folders include AHEP0731/2026-10-22 and CMB/2025-10-23.
Study-file collections and targeted-therapy exact strings have specific unit
coverage. An unreferenced LocalSearch workbook retains old Cypher and should not
be treated as the current CTDC query template.

### INS

Programs Explore compares Programs, Projects, Grants, and Publications against
`Programs.zip` TSV data through SQLite. Datasets Explore reads paginated cards
and compares Title, Source ID, Primary Disease, and Sample Count against CEDCD,
dbGaP, or GEO tables from `DataSetsTab.zip`.

The loader extracts missing TSV files and prefers flat Programs/DataSetsTab
bundles, with legacy dated-folder support. Existing extracted files are not
automatically replaced merely because a zip changes. Source freshness matters.
Publications is currently omitted from stat-bar comparison because its snapshot
lags ingestion; this does not disable the Publications result tab.

The Datasets Steps handler calls `app.verify_datasets_tab()`, but the INS adapter
defines `verify_datasets()`. This static dispatch mismatch affects the three
Datasets cases and has not been fixed in this learning pass.

### CCDI

The Hub currently has one static testcase. It has no independent Explore tables:
its Explore navigation hands off to C3DC. Do not add C3DC result tabs to the CCDI
adapter merely because the Hub links to them.

## Settings and outputs

`Commons/settings.py` loads `.env` without replacing existing process variables.
CLI selects environment/browser/headed behavior where provided; YAML supplies
defaults. Backend credentials and endpoints support app/environment-specific
overrides. `TEST_CASE_SOURCE` can override Excel collection. `INPUTFILES_ROOT`
and `OUTPUT_ROOT` can redirect file roots.

`TAB_ROW_LIMIT_<APP>` or `TAB_ROW_LIMIT` overrides the YAML row cap;
`PAGINATION_MAX_PAGES_<APP>` or its global form overrides the pagination cap.
`apply_tab_row_limit` replaces a trailing numeric LIMIT on tab queries. It does
not alter stat queries or unrestricted study-listing queries.

Static workbooks compare normalized text and links through `Static/<sheet>/<key>`
locators. Link comparison supports the implementation's path/hash normalization
and environment host rewriting. Static output is separate from tab comparisons.

The HTML reporter is enabled by environment settings, wraps action logging,
records query text and execution steps, and produces timestamped reports and a
latest alias. Failures can create screenshots. Treat outputs as run evidence,
not as automatically authoritative expected business rules.

## Validation baseline and open findings

`python3 -m pytest -m unit -q` initially produced **55 passed, two failed, 588 deselected**
in the learning pass. After adding runtime-parameter and participant-readiness tests, the current
run is **73 passed, two failed, 588 deselected**, with the same two failures. Both failures are assumptions about mutable configuration:

- `test_tab_row_limit_from_tab_setting_yaml`: GC expected 100; current YAML is 15.
- `test_app_settings_includes_tab_row_limit`: C3DC expected 100; current YAML is 13.

These were recorded without changing tests or row limits. No all-app UI regression
was run for this inventory. TC03 now validates the displayed record identities
through runtime bindings without changing its UI sort or saved Steps.

Static checks confirmed testcase input references, registered action names,
explicit tab/query mappings, filter groups and tokens, click locators, and static
sheet/object references. Direct method-call checks then identified the INS
Datasets dispatch mismatch described above.

Further findings to assess when working on the affected cases:

- Five phs000463 input workbooks retain 15 SQL tab queries under C3DC's Memgraph
  backend: GeneticAnalysisTab, TreatmentTab, and TreatmentRespTab in TC02, TC03,
  TC05, TC06, and TC07. Whether they execute depends on Steps, enabled tabs, and
  live counts. Syntax/backend incompatibility is observed; a live failure for
  each cell was not established by this inventory.
- The old CTDC LocalSearch workbook has four Cypher cells under the TSV app.
  It is not referenced by current testcase Steps.
- Five query workbooks have no current Steps row-2 reference: C3DC phs002371
  TC02 SexAtBirth-Female, TC10 TrtmntAgent-Unknown, TC13 FirstEven-Unknown;
  C3DC phs002430 TC02 SexAtBirth-Female; CTDC LocalSearch. This does not establish
  that they are safe to delete or unused by an external/manual workflow.
- One `~$...xlsx` under InputFiles/C3DC is an Excel lock file, not a workbook.
  It was left untouched and excluded from workbook parsing.

## Working on the next failure

Resolve the exact Steps and input reference first. Read applicable Cursor rules,
current config, relevant model/index references, and adapter tab wiring. Compare
the affected saved UI/DB sheet to distinguish a cohort mismatch, subset/ordering
problem, count scope, display transformation, stale source, or read/sync defect.

Fix the smallest authorized scope. For a query-only testcase request, change
only the affected input query cell. Verify its result against the intended
backend, compare every relevant column, then rerun the exact testcase. Confirm
other cells/styles remain intact. For shared code, run the relevant unit checks
and affected app cases. Report pre-existing failures and skipped checks plainly.

Useful commands from the repository root:

```bash
python3 -m pytest -m unit -q
python3 -m pytest -m "c3dc and quickrun" --env qa
python3 -m pytest -m "gc and smoke" --env qa
python3 -m pytest Testcases/C3DC/studies/phs002431/TC03_C3DC_phs002431_Race-HispOrLatino.xlsx --env qa
```

The index is dated evidence. Refresh affected entries and this guide after
meaningful changes; re-read current files and run evidence before making a fix.

## phs002431 Survival batch validation

TC01, TC02, and TC04 through TC08 were updated only in each input workbook's
Survival query cell. All other cells, formatting, and saved testcase Steps were
preserved against the files present when the batch began. No new framework
changes or UI sorting actions were added.

Queries were validated against QA and local C3DC Memgraph. Six cohorts returned
13 sample rows; TC04 Parotid Gland returned no Survival rows on either database.
Missing record identities returned no rows in all seven queries. The seven
original QA testcases passed in 346.94 seconds with two pytest workers. Six
Survival comparisons matched 13 rows and all five columns; TC04 skipped its
empty Survival tab. Saved UI/DB Survival sheets matched exactly. The current
HTML reporter skips xdist runs, so this validation has console results and
comparison workbooks rather than a new HTML report.

## Reported TC01 TC09 TC10 failures

TC01's failed output contained Female rows in a Male-filtered Participants grid
while stat counts already matched the Male cohort. Its participant query was
correct and was retained. C3DC now waits for visible rows to match both study and
checked Sex at Birth values, using the actual header position, and rechecks before
reading Participants. It does not accept wrong-sex records or introduce a fixed
sleep. Five unit cases cover stale/mixed grids, both predicates, multiple checked
sexes, reordered columns, and missing/incomplete data. A headed TC01 probe passed.

TC09 Immunotherapy and TC10 Bleomycin retained fixed Survival suffix lists outside
the earlier seven-case request. Their Survival cells now use the same runtime
selection pattern, preserving the original treatment predicates and every expected
field from Memgraph. Original testcase Steps and UI sorting remain unchanged.
The three original QA testcases passed together in headed Chromium in 125.21
seconds. TC01 also passed an earlier standalone headed probe. Saved Participants
rows were all Male and matched the database; both Survival sheets matched all
13 rows and five columns. Report: `Reports/C3DC_regression_20261104_165420.html`.

## phs002504 TC02 White Diagnosis page selection

The default Diagnosis request sorts only by Participant ID. In the reported
failure the UI placed valid `HM5085.dx21` at position 14; the query's secondary
Diagnosis ID ordering placed it at position 9, producing a different 13-row
subset. Do not exclude that record or alter the UI sorting.

`TC02_C3DC_phs002504_Race-White.xlsx`, DiagnosisTab B4, now establishes the study
and White participant cohort once, unions participant-linked and sample-linked
diagnoses, and binds `$ui_diagnosis_ids` from the currently displayed UI rows.
Only record identities come from the UI; all seven expected columns and cohort
membership come independently from Memgraph. QueryFile.bind_ui_rows supports
this opt-in parameter alongside the existing Survival parameter. Other testcase
queries retain their existing selection behavior.

QA and local queries matched all 13 rows and seven columns from the failed-run
UI output. The boundary record remained selectable when requested; nonexistent
identities returned no rows. Thirteen focused parameter tests passed. The full
QA testcase result was 1 passed in 57.10s. Only the Diagnosis query cell in
the workbook was changed; other cells, formatting, Steps, and UI sorting were
preserved.
