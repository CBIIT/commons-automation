# PSDC result tabs

Cases follow the C3DC layout: one folder per tab, TC01 for CSV and TC03 for sorting.
TC02 is reserved for JSON when the application exposes a JSON export control.

Sorting discovers enabled controls, verifies ascending/descending values across every page,
and checks exact row retention. Constant-value columns are reported as INCONCLUSIVE.
Sorting does not require a query workbook or database connection.

CSV cases load `InputFiles/PSDC/PSDC_ResultTabDownloads.xlsx`.
Each tab has a full export projection followed by a separate count query. Both bypass
display row limits. Verification requires every exported column and exact record membership;
it does not treat a successful download or matching row count as content validation.

Controls: `ObjectRepository/PSDC/result_tabs/<tab>.yaml`.
Export schemas: `Commons/apps/psdc/result_tabs.py`.

| Tab | Filters |
| --- | --- |
| Studies | None |

Run: `pytest Testcases/PSDC/result_tabs --env qa -q`

The inspected QA Explore tables expose CSV only, with no JSON menu.

The current dated TSV reference differs from live QA. CSV cases deliberately report those
differences. Refresh the expected TSV release to match the deployment before using these
cases as a required gate. Do not replace independent expectations with exported values.

## Validation observations

QA validation: sorting passed. The CSV comparison reports that PLCO differs between the TSV snapshot and deployment (participant and cancer-type totals).
