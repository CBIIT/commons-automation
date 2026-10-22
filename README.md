# Playwright + pytest UI automation

End-to-end regression framework for **Data Commons web apps**: open a browser, apply explore filters, read result tables from the UI, and compare them to expected data (usually **Memgraph Cypher** from per-test Excel workbooks). Tests are plain Python files run with **pytest**; each **application** (GC, C3DC, and others you add) gets its own app class, object repository, input data, and test tree.

Apps in the tree today include **GC**, **C3DC**, **ICDC**, and **CTDC** (plus locators for others). Each app follows the same folders: `Commons/apps/<app>.py`, `Testcases/<APP>/`, `InputFiles/<APP>/`, `ObjectRepository/<APP>/`.

## Framework map

Use this when you need to change something—not to memorize every module.

| If you need to… | Edit or run |
|-----------------|-------------|
| Run or write a test | `Testcases/<APP>/`, fixtures in `conftest.py`, app class in `Commons/apps/` |
| Portal URL or graph DB host | `Config/environments.yaml` (committed); passwords in gitignored `.env` |
| Fix a filter, tab, or stat-bar locator | `ObjectRepository/<app>/*.yaml` |
| Fix expected query or stat counts | `InputFiles/<app>/TC*.xlsx` columns `TabQuery`, `StatQuery` |
| Change how many tab rows UI vs DB compare | `Config/tab_setting.yaml` (`tab_row_limit` per app; env `TAB_ROW_LIMIT_<APP>`) |
| Skip a result tab (no UI/DB for that tab) | `Config/tab_setting.yaml` → `apps.<APP>.tabs.<TabName>: false` |
| Fix how the UI table is scraped | `Commons/table_reader.py` and tab settings in `Commons/apps/<app>.py` |
| Bulk-convert old SQL in Excel to Cypher | `Tools/convert_*_sql_to_cypher.py` and `Tools/cypher/` (**not** imported during pytest) |
| Regenerate tests from Katalon | `Tools/generate_tests.py`, `Tools/convert_object_repository.py` |

**Commons/** is the runtime library (what tests import). **Tools/** is maintenance and migration—ignore it until you refresh inputs or locators from legacy Katalon.

## What one test does

1. Load tab/stat queries from `InputFiles/<APP>/<case>.xlsx`
2. Navigate and dismiss banners
3. Open explore/data and set filters
4. Read the stat bar
5. For each result tab: open tab → read UI table → fetch expected rows → compare
6. Fail once at the end with every failed check listed (screenshot on failure)

Empty tabs (label shows **`(0)`**, e.g. Genetic Analyses) are **skipped**—no table scrape, no DB compare for that tab.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium    # and/or: playwright install firefox
cp .env.example .env           # gitignored; Memgraph passwords + optional run defaults
```

## Configuration

| Layer | Purpose |
|--------|---------|
| **`Config/environments.yaml`** | Per-app URLs and Memgraph host/username per `qa` / `stage` / `prod` (no secrets) |
| **`.env`** | `MEMGRAPH_PASSWORD_<APP>`, optional `ENV`, `BROWSER`, `HEADLESS` / `HEADED`, `SLOWMO`, `COMMONS_VERBOSE`, `FORCE_COLOR` |
| **`conftest.py`** | Session browser, `page` fixture, **`gc`** / **`c3dc`** fixtures (app opened at env URL) |
| **`pytest.ini`** | Markers: `gc`, `c3dc`, `smoke`, `regression`, `quickrun`, `static`, `unit` |

CLI flags override `.env` when both are set: `--env`, `--headed`, `--browser`, `--slowmo`, `--trace-actions`.

## Running tests

```bash
pytest -m unit                                    # library tests, no browser

pytest -m "gc and smoke"                          # one app + suite
pytest -m "c3dc and regression"
pytest -m quickrun

pytest Testcases/GC/studies/phs001437/test_TC01_GC_phs001437_Sex_Unknown_ExperimentalStrategy_RNASeq.py
pytest Testcases/C3DC/studies/phs000463/test_TC01_C3DC_phs000463_SexAtBirth_Female.py

pytest -k phs000463                               # by name fragment
pytest --env stage -m "gc and smoke"
pytest --headed --browser firefox <path-or-k>
pytest --trace-actions <test>                     # verbose steps (or COMMONS_VERBOSE=1 in .env)
pytest -n 4 -m "gc and regression"              # parallel (pytest-xdist)
pytest --junitxml=Reports/junit.xml
```

**Output:** per-check summary in the report (`Participants PASSED UI=13 DB=13`); row counts can match while a tab still **FAILED** (cell **DATA MISMATCH** — see stderr or the Checks section). Compare mismatches on stderr (red when terminal or `FORCE_COLOR=1`). Failures: `Reports/screenshots/`, `OutputFiles/<APP>/<ENV>/` → `*_UI.xlsx` / `*_DB.xlsx` with one sheet per result tab plus **`StatOutput`** for stat-bar counts (gitignored). Console prints Katalon-style stat lines when the bar is read and when DB expected counts are fetched.

### Expected data (graph DB)

| App | Engine | Excel | Credentials (examples) |
|-----|--------|--------|-------------------------|
| **C3DC**, **GC**, **CTDC** | Memgraph | Cypher in `TabQuery` / `StatQuery` | `MEMGRAPH_PASSWORD_<APP>` |
| **ICDC** | Neo4j | Same column layout | `NEO4J_PASSWORD_ICDC` (or legacy `MEMGRAPH_PASSWORD_ICDC`) |

Each app has its **own** cluster; do not share passwords. Tests read Cypher from the workbook— they do not import `Tools/cypher/`.

## Example tests

**C3DC** 

```python
@pytest.mark.c3dc
@pytest.mark.regression
def test_TC01_C3DC_example(c3dc):
    c3dc.load_query_file("TC01_C3DC_….xlsx")
    c3dc.accept_banner()
    c3dc.open_explore()
    c3dc.select_filter("Study/dbGaP_Accession", "phs000463")
    c3dc.select_filter("Demographics/SexAtBirth", "Female")
    c3dc.read_statbar()
    c3dc.verify_tab("Participants")
    c3dc.verify_tab("Studies")
    c3dc.verify_tab("Diagnosis")
    c3dc.verify_tab("Genetic Analysis")
    c3dc.verify_tab("Treatments")
    c3dc.verify_tab("Treatment Responses")
    c3dc.verify_tab("Survival")
    c3dc.verify_tab("Samples")
    c3dc.assert_no_failures()
```

Use the **`gc`** or **`c3dc`** fixture (defined in `conftest.py`); add a new fixture when you add an app to `Commons/apps/__init__.py` → `APPS`.

## Folder layout

```
Config/environments.yaml     URLs and DB hosts (no secrets)
Config/tab_setting.yaml      Tab row cap + which tabs verify_tab runs, per app
.env                         Passwords and local overrides (gitignored)

InputFiles/<app>/            TC*.xlsx — TabQuery / StatQuery for each test
ObjectRepository/<app>/      YAML — xpath keys for filters, tabs, static pages

Commons/                     Runtime (imported by pytest)
  settings.py                get_app_settings(), get_browser_settings()
  query_reader.py            Read query workbooks
  object_repository.py       YAML → xpath / filter groups
  db_source.py               Run Cypher over Bolt (Memgraph or Neo4j)
  apps/base.py               Filters, stat bar, verify_tab, assert_no_failures
  apps/{gc,c3dc,icdc,ctdc}.py
  table_reader.py, compare.py, browser_actions.py, static_data.py, …

Testcases/<APP>/             pytest tests
Testcases/unit/              Fast tests, no browser
conftest.py                  Browser + app fixtures

Tools/                       Scripts only (migration / generators)
  cypher/                    SQL → Cypher helpers for Excel refresh
  generate_tests.py, convert_object_repository.py, build_*_object_repository.py, …

OutputFiles/<app>/<env>/     UI/DB Excel from runs (gitignored)
Reports/                     Screenshots, JUnit
```

### Core API (per app instance)

| Step | Method |
|------|--------|
| Load queries | `load_query_file("TC….xlsx")` |
| Banner | `accept_banner()` |
| Enter explore | `open_data()` (GC) / `open_explore()` (C3DC) |
| Filter | `select_filter("Group/Name", "value")` — facet expand, dropdown, **checkbox click** (C3DC & GC) |
| Stat bar | `read_statbar()` |
| Result tab | `verify_tab("Participants")` — opens tab, reads UI, Memgraph, compare, stat bar once |
| End | `assert_no_failures()` |

Table pagination limits: **C3DC** `max_pages=2` per tab; **GC** `max_pages=10` (see `Commons/apps/*.py`). Table scraping rules live in `Commons/table_reader.py` (GC, ICDC, C3DC, INS, Bento, CTDC).

### Object repository (filters)

```yaml
# ObjectRepository/C3DC/filters/demographics.yaml (pattern for all filter groups)
groups:
  Demographics/Race:
    facet: (//*[text()="Demographics"])[1]
    dropdown: //*[@id='Race' and @role='button']
    checkboxes:
      Asian: //*[@id="checkbox_Race_Asian"]
      BlkAfricAmer: //*[@id="checkbox_Race_Black or African American"]
```

Add one `checkboxes` entry per value tests pass to `select_filter`. Some GC groups omit `facet` when the sub-filter opens without expanding the accordion; optional `search` / `dropdowns` / `other` stay as needed.

## Adding another application

1. **`Config/environments.yaml`** — `apps.<NAME>.urls`, optional `memgraph`, `expected_source`
2. **`Commons/apps/<name>.py`** — subclass `BaseApp`: `TABS`, `STATS`, navigation, filters if special
3. **`Commons/apps/__init__.py`** — register in `APPS`
4. **`ObjectRepository/<NAME>/`** — YAML locators
5. **`conftest.py`** — `@pytest.fixture def myapp(...)` using `_make_app("NAME", …)`
6. **`pytest.ini`** — `@pytest.mark.myapp` marker
7. **`Testcases/<NAME>/`** — tests; **`InputFiles/<NAME>/`** — Excel inputs

Regenerate or copy tests from Katalon with `Tools/generate_tests.py` and `Tools/convert_object_repository.py` when migrating legacy scripts.

## CI (Jenkins)

```bash
pip install -r requirements.txt && playwright install --with-deps chromium
# .env on the agent: MEMGRAPH_PASSWORD_GC=… MEMGRAPH_PASSWORD_C3DC=…
pytest -m "gc and smoke" --env qa -n 4 --junitxml=Reports/junit.xml
```

Map legacy suite names to pytest markers (e.g. CDS_Smoke → `-m "gc and smoke"`, profile → `--env`).

## Behaviour notes

- **Compare:** rows sorted left-to-right, then positional cell compare; ✓ / ✗ console output; row-count mismatch fails.
- **Deferred failure:** all tabs run; failures collected; one `AssertionError` at `assert_no_failures()`.
- **Skip:** stat bar count 0 for that tab’s gate stat, or selected tab label **`(0)`**.
- **Katalon migration:** optional Tools and marker naming preserved where useful; exact historical test counts are not maintained in this doc—use `pytest --collect-only -m "<marker>"`.

## Known gaps

- C3DC/GC filter YAML must stay aligned with Explore/Data UI (`CCDI-C3DC-Integrated-UI`, General Commons). Re-check locators after UI releases.
- Previously skipped conversion cases (missing checkboxes) are enabled; run headed once if a filter xpath drifts—see `pytest -rs` for any remaining skips.
