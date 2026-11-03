# commons-automation

Playwright + pytest UI regression for NCI Data Commons portals. Each test applies Explore filters, reads stat bar and result tables from the UI, and compares them to expected data from **Memgraph/Neo4j (Cypher)** or **TSV + SQL (CTDC, INS)**.

Supported apps: **GC**, **C3DC**, **ICDC**, **CTDC**, **INS**, **Bento**, **CCDI** (Hub → C3DC Explore).

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
| Secrets | `.env` (`MEMGRAPH_PASSWORD_<APP>`, …) |
| Tab on/off, row limit | `Config/tab_setting.yaml` |
| Locators | `ObjectRepository/<APP>/` |
| Queries / stat SQL or Cypher | `InputFiles/<APP>/TC*.xlsx` (`TabQuery`, `StatQuery`) |
| Portal-specific behavior | `Commons/apps/<app>.py`, `Commons/table_reader.py` |
| Tests | `Testcases/<APP>/` |

Per-app layout: `Commons/apps/<app>.py`, `Testcases/<APP>/`, `InputFiles/<APP>/`, `ObjectRepository/<APP>/`. **Tools/** is Katalon migration only—not used at pytest runtime.

## Expected data

| App | Source | Workbook | Password env |
|-----|--------|----------|--------------|
| GC, C3DC | Memgraph | Cypher | `MEMGRAPH_PASSWORD_<APP>` |
| ICDC, Bento | Neo4j | Cypher | `NEO4J_PASSWORD_*` |
| CTDC, INS | TSV snapshots + in-memory SQL | SQL | none |

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

`verify_tab` runs all enabled tabs in the app unless you call it per tab. Empty tabs `(0)` are skipped. Failures are collected until `assert_no_failures()` (screenshot under `Reports/screenshots/`; compare workbooks under `OutputFiles/<APP>/<env>/`).

## CI

Install deps + Playwright browser, set `.env` passwords on the agent, then e.g. `pytest -m "gc and smoke" --env qa -n 4 --junitxml=Reports/junit.xml`.
