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

## Test shape

Each case is a **`TC*.xlsx`** under `Testcases/<APP>/` (for example `Testcases/C3DC/studies/phs000463/TC01_C3DC_phs000463_SexAtBirth-Female.xlsx`). Pytest collects it when `framework.test_case_source` is **`excel`**; **`Config/suites.yaml`** assigns markers such as `smoke` and `regression`.

## CI

Install deps + Playwright browser, set `.env` passwords on the agent, then e.g. `pytest -m "gc and smoke" --env qa -n 4 --junitxml=Reports/junit.xml`.
