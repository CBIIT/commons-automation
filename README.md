# commons-automation

Playwright + pytest UI regression for NCI Data Commons portals. Each test applies Explore filters, reads stat bar and result tables from the UI, and compares them to expected data from **Memgraph/Neo4j (Cypher)** or **TSV + SQL (CTDC, INS)**.

Supported apps: **GC**, **C3DC**, **ICDC**, **CTDC**, **INS**, **Bento**, **CCDI** (Hub → C3DC Explore).

## How it works

Two kinds of Excel file: **test case** workbooks under `Testcases/<APP>/studies/…/TC*.xlsx` (Steps: actions only) and **query** workbooks under `InputFiles/<APP>/TC*.xlsx` (Cypher/SQL for stat bar and tabs). **GC**, **CTDC**, **C3DC**, **ICDC**, and **Bento** explore studies use test-case Excel when `framework.test_case_source: excel`; other apps still use Python tests that call the adapter directly.

```
                         ┌──────────────────────┐
                         │  pytest + conftest   │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┴─────────────────────┐
              │        collect Testcases/…/TC*.xlsx       │            
              └─────────────────────┬─────────────────────┘
                                    │
                         ┌──────────▼───────────┐
                         │ excel_test_runner      │  (Steps sheet → adapter calls)
                         │ or test function body  │
                         └──────────┬─────────────┘
                                    │
                         ┌──────────▼───────────┐
                         │  App adapter (C3DC,  │
                         │  GC, CTDC, INS, …)   │
                         └──┬─────────┬─────────┬─┘
              ┌──────────────┘         │         └──────────────┐
              ▼                        ▼                        ▼
     ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
     │ Playwright + UI │    │ ObjectRepository│    │ InputFiles      │
     │ (scrape tables) │    │ YAML locators   │    │ TC*.xlsx queries│
     └────────┬────────┘    └─────────────────┘    └────────┬────────┘
              │                                              │
              │              ┌───────────────────────────────┘
              │              ▼
              │     ┌─────────────────┐     ┌──────────────────┐
              └────►│ compare_tables  │◄────│ ExpectedDataSource│
                    │ + stat compare  │     │ Memgraph / Neo4j │
                    └────────┬────────┘     │ or TSV + SQL     │
                             │              └──────────────────┘
                             ▼
                    *_UI.xlsx / *_DB.xlsx, HTML report
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
pytest -m unit                                    # no browser
pytest -m "c3dc and regression" --env qa          # Python study tests (most apps)
pytest -m "gc and regression" --env qa            # GC explore: TC*.xlsx under studies/
pytest --headed Testcases/GC/studies/phs000720/   # one study folder (excel mode)
pytest --headed Testcases/C3DC/studies/phs000463/test_TC01_C3DC_phs000463_SexAtBirth_Female.py
```

Use app fixtures from `conftest.py` (`gc`, `c3dc`, `ctdc`, `ins`, …). Markers in `pytest.ini`: `smoke`, `regression`, `static`, `datarelease` (C3DC release batch), etc. CLI: `--env`, `--headed`, `--browser`, `--trace-actions`.

## Where to change things

| Need | Location |
|------|----------|
| URLs, DB hosts, TSV roots | `Config/environments.yaml` |
| Secrets | `.env` (`MEMGRAPH_PASSWORD_<APP>`, …) |
| Excel vs Python test steps | `Config/environments.yaml` → `framework.test_case_source` (`excel` collects `TC*.xlsx` under `Testcases/<APP>/studies/…`) |
| Tab on/off, row limit | `Config/tab_setting.yaml` |
| Locators | `ObjectRepository/<APP>/` |
| Query / expected data (Cypher or SQL) | `InputFiles/<APP>/TC*.xlsx` (`TabQuery`, `StatQuery`) |
| Excel step definitions (GC / CTDC / C3DC / ICDC / Bento) | `Testcases/<APP>/…/TC*.xlsx` (`studies/` or `arm-*/`); per-app: `Commons/excel_testcase/apps/`; convert: `Tools/convert_study_tests_to_excel.py <APP_KEY>` |
| Portal-specific behavior | `Commons/apps/<app>.py`, `Commons/table_reader.py` |
| Tests | `Testcases/<APP>/` (Python and/or testcase Excel) |

Per-app layout: `Commons/apps/<app>.py`, `Testcases/<APP>/`, `InputFiles/<APP>/`, `ObjectRepository/<APP>/`. **GC, CTDC, C3DC, ICDC, and Bento** use `TC*.xlsx` when `framework.test_case_source: excel` (see `Commons/excel_testcase/README.md` to add INS/…). Maintainer scripts: **`Tools/README.md`** (not used at pytest runtime).

## Expected data

| App | Source | Workbook | Password env |
|-----|--------|----------|--------------|
| GC, C3DC | Memgraph | Cypher | `MEMGRAPH_PASSWORD_<APP>` |
| ICDC, Bento | Neo4j | Cypher | `NEO4J_PASSWORD_*` |
| CTDC, INS | TSV snapshots + in-memory SQL | SQL | none |

## Test shape

**Python (C3DC, CTDC, …)** — decorators supply markers; the test calls the adapter:

```python
@pytest.mark.c3dc
@pytest.mark.regression
def test_example(c3dc):
    c3dc.load_query_file("TC01_C3DC_….xlsx")
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter("Demographics/SexAtBirth", "Female")
    c3dc.read_statbar()
    c3dc.verify_tab("Participants")
    c3dc.assert_no_failures()
```

**GC / CTDC / C3DC / ICDC / Bento (Excel testcase)** — row 2 points at `InputFiles/<APP>/…`; following rows are Action/Page/Params/Filter (`open_data`, `open_explore`, `open_cases`, `set_age_range`, filters, `verify_tab`, …). Pytest applies the app marker, `regression`, and `smoke` (for `TC01_*`) at collection time—no `.py` per case.

`verify_tab` runs all enabled tabs in the app unless you call it per tab. Empty tabs `(0)` are skipped. Failures are collected until `assert_no_failures()` (screenshot under `Reports/screenshots/`; compare workbooks under `OutputFiles/<APP>/<env>/`).

## CI

Install deps + Playwright browser, set `.env` passwords on the agent, then e.g. `pytest -m "gc and smoke" --env qa -n 4 --junitxml=Reports/junit.xml`.
