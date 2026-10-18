# commons-automation

Playwright + pytest version of the Katalon `Commons_Automation` framework, for **GC** (General Commons) and **C3DC**.
Same idea as before: apply filters in the UI, read what the UI shows, and compare it with the expected data
from the input Excel files. Now every test is a plain Python file, and you can run it alone, as a smoke
suite, or as a regression suite.

## Setup (once)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## Running tests

```bash
pytest -m unit                              # Commons self-tests, no browser or network (2 seconds)

pytest -m "gc and smoke"                   # GC smoke suite        (88 tests, = Katalon CDS_Smoke)
pytest -m "gc and regression"              # GC regression         (193 tests, = CDS_Regression_Full)
pytest -m "c3dc and smoke"                  # C3DC smoke suite
pytest -m "c3dc and regression"             # C3DC regression
pytest -m quickrun                          # the QuickRun suites

pytest Testcases/gc/studies/phs001437/test_TC01_GC_phs001437_Sex_Unknown_ExperimentalStrategy_RNASeq.py   # ONE test
pytest -k phs001437                         # every test whose name contains phs001437
pytest -k "TC01 and phs001437"

pytest --env stage -m "gc and smoke"       # environment: qa (default) | stage | prod
pytest --headed --slowmo 300 <test>         # watch the browser
pytest --trace-actions <test>               # Katalon-style console log (xpaths, every UI/DB cell)
# or: COMMONS_VERBOSE=1 in .env
pytest --browser firefox <test>             # chromium (default) | firefox | webkit
pytest -n 4 -m "gc and regression"         # 4 tests in parallel (needs pytest-xdist, in requirements)
```

Results: the terminal shows one line per check (`Participants PASSED UI=8 expected=8`); on failure it prints the
rows that differ. A screenshot of the failing page goes to `Reports/screenshots/`, and what the UI showed and what
was expected go to `OutputFiles/<app>/<ENV>/<test>_UI.xlsx` / `_DB.xlsx` (e.g. `OutputFiles/GC/QA/…`; worksheets named e.g. `UI_Participants`, `DB_Participants`; folder is gitignored and created on run).
`pytest --junitxml=Reports/junit.xml` gives a JUnit file for Jenkins.

### Where "expected data" comes from

| App | Source | What you need |
|---|---|---|
| **C3DC** | Cypher in the input Excel, run against **Memgraph** | Host/username: `apps.C3DC.memgraph` in `Config/environments.yaml`. Password: **`MEMGRAPH_PASSWORD_C3DC`** in `.env` (only). |
| **GC** | Cypher in the input Excel, run against **Memgraph** | Host/username: `apps.GC.memgraph`. Password: **`MEMGRAPH_PASSWORD_GC`**. C3DC and GC do **not** share Memgraph credentials. |

**Memgraph auth (`Authentication failure`)** — wrong password for that app’s Bolt host, or still using legacy `MEMGRAPH_PASSWORD` (ignored now). Set the matching `MEMGRAPH_PASSWORD_<APP>` key. Passwords are never in YAML.

## How a test looks

```python
@pytest.mark.gc
@pytest.mark.smoke
def test_TC01_GC_phs001437_Sex_Unknown_ExperimentalStrategy_RNASeq(gc):
    gc.load_query_file("TC01_GC_phs001437_Sex-Unknown_ExperimentalStrategy-RNASeq.xlsx")
    gc.accept_banner()
    gc.open_data()
    gc.select_filter("StudyFacet/PHS_Accession", "phs001437")
    gc.select_filter("DemographicsFacet/Sex", "Unknown")
    gc.select_filter("StudyFacet/ExperimentalStrategy", "RNASeq")
    gc.read_statbar()
    gc.verify_tab("Participants")
    gc.verify_tab("Samples")
    gc.verify_tab("Files")
    gc.assert_no_failures()
```

| Katalon | Here |
|---|---|
| `RunKatalon('X.xlsx')` | `app.load_query_file("X.xlsx")` |
| `clickTab('.../WarningBan_Continue_Btn')` | `app.accept_banner()` |
| `clickTab(Explore-Tab)` / `clickTabCDSStat(CDS_Data-Btn)` | `app.open_explore()` / `app.open_data()` (GC: `NavBar/GC_Data-Btn`) |
| filter facet + dropdown + checkbox (3 clicks) | `app.select_filter("Study/dbGaP_Accession", "phs000466")` |
| `readStatBarC3DC / readStatBarCDS` | `app.read_statbar()` |
| `openTab` + `multiFunction(...)` (10 arguments) | `app.verify_tab("Participants")` |
| `ReadCasesTableKatalon` (per-app switches) | `Commons/table_reader.py` — `read_table_header_data` / `read_table_row_data`; pagination via `max_pages` on `TabSpec` in `Commons/apps/*.py` |
| `validateStatBar` | done inside `verify_tab` |
| `WebUI.waitForElementPresent`, `WebUI.delay`, `Thread.sleep` | gone, Playwright waits automatically |
| `KeywordUtil.markFailed` (stops at first failure) | all tabs are checked, then the test fails once with every difference listed |
| `ReadExcel.Memgraph` / ConnectMemgraph | `Commons/memgraph_source.py` (`MemgraphSource`, no subprocess) |

## Folder map

```
Config/environments.yaml     URLs per env, expected-data source per app           (Katalon: Profiles/*.glbl)
ObjectRepository/<app>/     locators, one YAML per page or facet
InputFiles/<app>/              input Excel files (+ C3DC TSV data)
Commons/                     browser actions, table reader, compare, Memgraph, app objects
Commons/apps/{c3dc,gc}.py  per-app config: tabs, stat bar, navigation
Testcases/<app>/...           the test cases, same folder layout as Katalon
conftest.py                  browser + fixtures (`c3dc`, `gc`), --env, --headed
Tools/                       converters (see below)
Reports/                     screenshots, JUnit (git-ignored except .gitkeep)
OutputFiles/                 UI/DB Excel per run: <app>/<ENV>/ (git-ignored, created on run)
```

### Object repository

`ObjectRepository/gc/data_page/filter/study_facet.yaml` (abridged):

```yaml
page: Data_page/Filter/StudyFacet
groups:
  StudyFacet/PHS_Accession:
    dropdown: //*[@id="PHS Accession"]/div[2]
    search: //input[@placeholder='e.g. phs000000']
    checkbox_template: //*[@id="checkbox_PHS Accession_{value}"]     # any study works, no new locator
    checkboxes:                                                      # only the irregular ones
      phs001554: //*[@id='checkbox_PHS Accession_phs001554']
```

`{value}` is the token from the Katalon object name (`phs001437_Chkbx` -> `phs001437`). A value that is not
in `checkboxes:` and has no template raises an error listing the known values.
Plain elements are looked up by `Folder/Name`, e.g. `app.click("NavBar/GC_Data-Btn")`.
Katalon's 284 (C3DC) + 453 (GC) `.rs` files became 32 YAML files.

## Jenkins

Replace the Katalon step with:

```bash
pip install -r requirements.txt && playwright install --with-deps chromium
# copy `.env.example` → `.env` (gitignored; auto-loaded), e.g. MEMGRAPH_PASSWORD_C3DC=... and MEMGRAPH_PASSWORD_GC=...
pytest -m "gc and smoke" --env qa -n 4 --junitxml=Reports/junit.xml
```

`jenkins/Test-Schedule.csv` rows map straight onto this: `Katalon_Suite` becomes a `-m` expression
(`Test Suites/CDS_Smoke` -> `-m "gc and smoke"`) and `Profile` becomes `--env`.

## Adding a test

1. Put the input Excel in `InputFiles/<APP>/`.
2. Copy any existing test file and change the Excel name and the `select_filter` lines, or re-run the generator.
3. Add `@pytest.mark.smoke` / `@pytest.mark.regression` to put it in a suite.

## Tools

```bash
python Tools/convert_object_repository.py --katalon ../Commons_Automation --apps C3DC GC   # .rs XML -> YAML
python Tools/generate_tests.py            --katalon ../Commons_Automation --apps C3DC GC   # Katalon scripts + suites -> Testcases/
```

The generator turned 553 Katalon scripts into 553 test files (238 C3DC + 315 GC); with the 2 hand-written
static-page tests that is **555 tests**. Suite membership is copied from the `.ts` suites, and the marker counts match
Katalon exactly (GC smoke 88, regression 193, quickrun 14; C3DC smoke 21, regression 151, quickrun 2).

Not generated on purpose: the two standalone Python quick-run scripts (`TC00_C3DC_QuickRun_Of_TsvFiles`,
`GC_QuickRunupdates`), and the two `*_StaticData` tests, which are hand-written.

**11 tests are marked `skip`** (see `pytest -rs`). Their Katalon script clicks a checkbox that has no locator in the
Katalon Object Repository either, so they could not have passed there. Typical causes are a typo in the script
(`phs0002517`, `Imaging Facet` with a space) or a value that was never added (`Saliva`, `Illumina`).
Fix the script value or add the locator under `checkboxes:` in the facet's YAML and delete the `skip` line.

## Differences from Katalon worth knowing

* **Row comparison** follows Katalon `compareSheetsByRow` / `compareTwoLists`: both sides are sorted by whole row,
  compared positionally, with the same cell-by-cell console output (match ✓ / mismatch ✗).
* **A different row count is a failure.** Katalon passed when the expected side returned no rows.
* **All rows are read.** Katalon stopped after 10 pages.
* **Table reads** — `read_table_data` → **GC, ICDC, C3DC, INS, Bento, CTDC** (that order in `read_table_header_data` / `read_table_row_data`). GC `first_child=True` on `TabSpec`. Env: `G_ROWCOUNT_FILES`, `G_ROWCOUNT_KATALON`.
* CPI-badge stripping and multi-value (`a;b`) normalisation are the same rules as `Utils.groovy`.
* The CDS_PROD Katalon profile pointed at the stage URL; `prod` here points at production.

## Known issues

* **C3DC filters without URL mapping** (e.g. age sliders, some sample facets) still use legacy checkbox XPaths and may
  need UI clicks updated. Common study/demographics/diagnosis/survival filters are applied via Explore Participants
  query parameters in `Commons/apps/c3dc.py`.
* In the C3DC Object Repository, `Study/StudyName` has `MolecularCharacterizationInitiative` and
  `TargetNeuroblastoma` pointing at each other's XPath. Carried over as-is.
