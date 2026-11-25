# commons-automation

Playwright + pytest UI regression for NCI Data Commons portals. Each test applies Explore filters, reads stat bar and result tables from the UI, and compares them to expected data from **Memgraph/Neo4j (Cypher)** or **TSV + SQL (CTDC, INS, PSDC)**.

Supported apps: **GC**, **C3DC**, **ICDC**, **CTDC**, **PSDC**, **INS**, **Bento**, **CCDI** (Hub → C3DC Explore).

New to the project? Start with the [onboarding guide](docs/ONBOARDING.md).

## How it works

With `framework.test_case_source: excel` in `Config/environments.yaml`, pytest collects **`TC*.xlsx`** under `Testcases/<APP>/`. Each workbook’s **Steps** sheet drives the run (`Commons/excel_testcase/`); row 2 points at the matching query workbook in **`InputFiles/<APP>/`**. Suite membership (`quickrun`, `smoke`, `regression`, …) comes from **`Config/suites.yaml`**. Override with `TEST_CASE_SOURCE=python` to use legacy `test_*.py` where those files still exist.

```
                         ┌──────────────────────┐
                         │  pytest + conftest   │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │  Excel testcase layer│
                         │  Testcases/TC*.xlsx  │
                         │  Steps → runner      │
                         └──────────┬───────────┘
                                    │
                         ┌──────────▼───────────┐
                         │  App adapter (C3DC,  │
                         │  GC, CTDC, INS, …)   │
                         └──┬─────────┬───────┬─┘
              ┌─────────────┘         │       └──────────────┐
              ▼                       ▼                      ▼
     ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
     │ Playwright + UI  │   │ ObjectRepository │   │ InputFiles       │
     │ (scrape tables)  │   │ YAML locators    │   │ TC*.xlsx queries │
     └────────┬─────────┘   └──────────────────┘   └────────┬─────────┘
              │                                             │
              │                                          ┌──┘
              │                                          ▼
              │     ┌──────────────────┐          ┌──────────────────┐
              └────►│ compare_tables   │◄──------ │ Expected Data src│
                    │ + stat compare   │          │ Memg / Neo4j/TSV │
                    └─────────┬────────┘          └──────────────────┘    
                              │            
                              ▼
         OutputFiles: *_UI.xlsx / *_DB.xlsx, HTML report
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # Memgraph/Neo4j passwords; optional ENV, HEADLESS, HTML_REPORT
```

## Run tests

```bash
pytest -m unit                          # no browser
pytest -m "c3dc and regression" --env qa
pytest --headed Testcases/C3DC/studies/phs000463/TC01_C3DC_phs000463_SexAtBirth-Female.xlsx --env qa
```

Use app fixtures from `conftest.py` (`gc`, `c3dc`, `ctdc`, `ins`, …). Markers in `pytest.ini`: `smoke`, `regression`, `static`, `datarelease` (C3DC release batch), etc. CLI: `--env`, `--headed`, `--browser`, `--trace-actions`.

## Where to change things

| Need | Location |
|------|----------|
| URLs, DB hosts, TSV roots | `Config/environments.yaml` |
| Secrets | `.env` (`<APP>_DB_PASSWORD_<ENV>`, …) |
| Tab on/off, row limit | `Config/tab_setting.yaml` |
| Locators | `ObjectRepository/<APP>/` |
| Queries / stat SQL or Cypher | `InputFiles/<APP>/TC*.xlsx` (`TabQuery`, `StatQuery`) |
| Portal-specific behavior | `Commons/apps/<app>/app.py` and feature helpers; shared table reading in `Commons/table_reader.py` |
| Tests | `Testcases/<APP>/` |

Per-app layout: `Commons/apps/<app>/`, `Testcases/<APP>/`, `InputFiles/<APP>/`, `ObjectRepository/<APP>/`.

File-cart adapters in `Commons/apps/<app>/file_cart.py` inherit directly from
`Commons.file_cart.FileCart`. The shared class owns reusable cart mechanics;
app adapters own column mappings, manifest schemas, messages, rendering options,
navigation, and behavior overrides.

Result-tab export mechanics live in `Commons/result_tabs.py`, with app-specific
controls and schemas in `Commons/apps/<app>/result_tabs.py`. C3DC objects are
grouped per tab under `ObjectRepository/C3DC/result_tabs/`; test cases follow
`Testcases/C3DC/result_tabs/<tab>/`. The CSV cases for all six result tabs filter
only by `Abdominal fibromatosis` and verify all exported columns
against Memgraph. Its query workbook has a `Parameters` sheet for the
diagnosis and query safety limit. Export queries bypass display row limits,
and an independent count query fails verification if expected data is truncated.
JSON cases for all six tabs check the full typed record, including arrays, nulls,
and internal IDs, against each tab's `*JSONExportTab` query. Federated Participants
CPI mappings are checked against a separate `participantOverview` API request for the database's
participant IDs. Participant clinical array order remains significant. Other tabs
compare unordered metadata arrays by complete values; duplicate values remain significant. Shared file
names must match an alias from the database for that file GUID.

Sorting checks use `Commons/table_sorting.py` through
`app.verify_result_tab_sorting("Participants", report_name)` or the shared Excel action
`verify_result_tab_sorting` (Page = tab name). The checker discovers enabled ARIA/MUI
sort controls, skips non-sortable columns, checks ascending and descending order,
and compares complete row membership across every page. It refuses truncated
baselines; filter large tables to fewer than 500 rows or adjust `SortingOptions`.
Applications can override `result_tab_sorting_options()` for column types, multi-value
sort keys, link destinations, or response readiness. C3DC TC03 sorting cases cover all
six result tabs using only Abdominal fibromatosis. Files and Imaging Data retain that
filter when switching to Explore Files. Checks wait for the exact field/direction
response, or a previously observed cached order. Complete investigator names are
preserved despite embedded commas, and viewer columns compare actual URLs.
Evidence is saved as `<tab>_sorting.json` under the test case's
`OutputFiles/.../result_tabs/` folder. Constant-value directions are reported as
inconclusive rather than counted as meaningful order checks.

Page-size and pagination checks live in `Commons/table_pagination.py`; sorting and
pagination share `Commons/table_navigation.py` for table snapshots and Next/Previous
navigation. Call `app.verify_result_tab_pagination("Files", page_sizes=[50, 100])`, or
use the shared Excel action `verify_result_tab_pagination` with the tab in Page and
comma-separated sizes in Params. Omit sizes to discover all positive numeric choices;
an explicitly required unavailable size fails rather than being skipped.
The checker verifies every forward/backward page, ranges, row counts, disabled boundary
controls, complete data retention, and size changes from a later page. It returns to
the first page at the original size. App adapters provide identities, independent
result counts, custom control keys, or expected resizing behavior.
C3DC TC04 cases for all six result tabs use only Abdominal fibromatosis and require the
currently offered 50/100-row sizes. The common native/MUI tests also exercise 10/25,
empty/small result sets, exact page boundaries, and alternative resizing policies.
Evidence is saved as `<tab>_pagination.json` in the test case's output folder.

### Result-tab coverage in other applications

The C3DC layout is reused under `Testcases/<APP>/result_tabs/<tab>/`:

| Application | CSV cases | JSON cases | Sorting cases |
| --- | ---: | ---: | ---: |
| C3DC (existing) | 6 | 6 | 6 |
| GC | 3 | No UI control | 3 |
| CTDC | 4 | No UI control | 4 |
| ICDC | 4 | No UI control | 4 |
| INS | 4 | No UI control | 4 |
| PSDC | 1 | No UI control | 1 |
| Bento | No UI control | No UI control | 3 |

`DirectCSVResultTabs` reuses the same download capture, strict file parsing,
independent count checks, and complete-record comparison as C3DC. Application
adapters own schemas, query keys, and rendering semantics. SQL/Cypher projections
are organized by tab in `<APP>_ResultTabDownloads.xlsx`, with visible gridlines
and compact rows. Per-app result-tab READMEs list the filters and run commands.
CTDC and PSDC currently expose differences from the dated TSV references; the
CSV checks retain those failures rather than accepting live exports as expected data.

## Expected data

| App | Source | Workbook | Password env |
|-----|--------|----------|--------------|
| GC, C3DC | Memgraph | Cypher | `<APP>_DB_PASSWORD_<ENV>` |
| ICDC, Bento | Neo4j | Cypher | `<APP>_DB_PASSWORD_<ENV>` |
| CTDC, INS, PSDC | TSV snapshots + in-memory SQL | SQL | none |

CTDC node TSVs live under `InputFiles/CTDC/<STUDY>/YYYY-MM-DD/`. INS keeps `Programs.zip` / `DataSetsTab.zip` in git; the first test run extracts `InputFiles/INS/Programs/` (node TSVs) and dated folders under `InputFiles/INS/` or `DataSetsTab/` (gitignored—do not commit). When publication counts drift, refresh the zips from [ins-data](https://github.com/CBIIT/ins-data) and remove `stat_bar_omit` for Publications in `Config/environments.yaml`.

## Test shape

Each case is a **`TC*.xlsx`** under `Testcases/<APP>/` (for example `Testcases/C3DC/studies/phs000463/TC01_C3DC_phs000463_SexAtBirth-Female.xlsx`). Pytest collects it when `framework.test_case_source` is **`excel`**; **`Config/suites.yaml`** assigns markers such as `smoke` and `regression`.

The **Steps** sheet is the test script. **Row 2** (`Input Excel`) must point at the query workbook in `InputFiles/<APP>/` (Cypher/SQL tabs). Following rows are adapter actions (`Action`, `Page`, `Params`, `Filter`):

| Input Excel | Action | Page | Params | Filter |
|-------------|--------|------|--------|--------|
| `InputFiles/C3DC/TC01_C3DC_phs000463_SexAtBirth-Female.xlsx` | | | | |
| | `accept_banner` | | | |
| | `open_explore` | | | |
| | `select_filter` | Study/dbGaP_Accession | | phs000463 |
| | `select_filter` | Demographics/SexAtBirth | | Female |
| | `read_statbar` | | | |
| | `verify_tab` | | Participants | |
| | `assert_no_failures` | | | |

Run one file: `pytest Testcases/C3DC/studies/phs000463/TC01_C3DC_phs000463_SexAtBirth-Female.xlsx --env qa`

`verify_tab` checks the tab named in `Params`; `verify_all_tabs` checks the app's standard enabled tabs. Empty tabs `(0)` are skipped. Failures are collected until `assert_no_failures()` (screenshot under `Reports/screenshots/`; compare workbooks under `OutputFiles/<APP>/<ENV>/`).

## CI

Install deps + Playwright browser, set `.env` passwords on the agent, then e.g. `pytest -m "gc and smoke" --env qa -n 4 --junitxml=Reports/junit.xml`.
