# Developer onboarding

Playwright and pytest test NCI Data Commons portals. Excel testcase workbooks define UI steps; separate input workbooks supply queries or expected static content.

## 1. Set up your workspace

Python 3.12 is recommended. Run commands from the repository root and confirm access to the target portal and data source, including VPN access when required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
cp .env.example .env
```

Copy `.env.example` only for a new setup. Set the required passwords, such as `GC_DB_PASSWORD_QA`. `.env` loads automatically; shell variables take precedence. Never commit credentials.

Check [environment configuration](../Config/environments.yaml) for URLs and connections. GC/C3DC use Memgraph; ICDC/Bento use Neo4j; CTDC/INS/PSDC use TSV releases with SQL. Obtain the matching release before testing. PSDC reads approved files from `<STUDY>/YYYY-MM-DD/`, not ZIPs automatically.

## 2. Make your first run

```bash
# Check the framework without a browser or database.
python -m pytest -m unit -q

# Run one static-content case on GC QA.
python -m pytest Testcases/GC/static/TC01_GC_StaticData.xlsx --env qa

# Start small before running a full regression.
python -m pytest -m "gc and quickrun" --env qa
python -m pytest -m "gc and regression" --env qa
```

To watch locally, append `--headed --slowmo 500`. Quote paths containing spaces. Select the environment explicitly.

## 3. Know where changes belong

The execution flow is **Excel steps → runner → app adapter → UI and expected-data source → comparison and report**.

| Location | Responsibility |
| --- | --- |
| [Testcases/](../Testcases/) | `TC*.xlsx` workbooks describing test steps |
| [InputFiles/](../InputFiles/) | Cypher/SQL workbooks, static expectations and source data |
| [ObjectRepository/](../ObjectRepository/) | App-specific YAML locators and filter values |
| [Commons/apps/](../Commons/apps/) | App adapters and feature helpers |
| [Commons/excel_testcase/](../Commons/excel_testcase/README.md) | Excel action dispatch and app profiles |
| [Config/](../Config/) | Environments, tab settings and suite membership |

Keep portal behavior in its app package. Shared-code changes need a cross-app reason and focused unit tests.

## 4. Add or update a testcase

1. Copy a passing case from the same app and feature.
2. Use the `Steps` columns: `Input Excel`, `Action`, `Page`, `Params`, `Filter`. Row 2 identifies the input workbook; actions begin at row 3.
3. Reuse registered actions and YAML filter tokens. Put reusable behavior in app helpers.
4. Match query columns and ordering to the UI. Derive expectations from the configured source; validate query plans and timing. Never hardcode observed totals.
5. End comparison cases with `assert_no_failures`. Verify collection and suite membership in [suites.yaml](../Config/suites.yaml).
6. Run the case and inspect its output. On renames, update paired filenames, input references and stored output names. Preserve formatting and gridlines.

Consult the [project rules](../.cursor/rules/) and [query skills](../.cursor/skills/) for app-specific conventions.

## 5. Review results and run in CI

Open `Reports/latest.html`. Comparison workbooks and functional evidence are in `OutputFiles/<APP>/<ENV>/`; failure screenshots are in `Reports/screenshots/`.

For mismatches, inspect output columns and values before changing expectations. For locator timeouts, inspect the UI. Use `--collect-only -q` for missing tests and `--trace-actions` for action logs.

CI uses the same commands headlessly. Install dependencies and Chromium, inject credentials through CI secrets, and retain `Reports/` and `OutputFiles/` as artifacts. Parallel runs (`-n`) skip custom HTML; use `--junitxml=Reports/junit.xml`, or omit `-n` when HTML is required.
