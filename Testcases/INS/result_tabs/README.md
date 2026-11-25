# INS result tabs

Cases follow the C3DC layout: one folder per tab, TC01 for CSV and TC03 for sorting.
TC02 is reserved for JSON when the application exposes a JSON export control.

Sorting discovers enabled controls, verifies ascending/descending values across every page,
and checks exact row retention. Constant-value columns are reported as INCONCLUSIVE.
Sorting does not require a query workbook or database connection.

CSV cases load `InputFiles/INS/INS_ResultTabDownloads.xlsx`.
Each tab has a full export projection followed by a separate count query. Both bypass
display row limits. Verification requires every exported column and exact record membership;
it does not treat a successful download or matching row count as content validation.

Controls: `ObjectRepository/INS/result_tabs/<tab>.yaml`.
Export schemas: `Commons/apps/ins/result_tabs.py`.

| Tab | Filters |
| --- | --- |
| Programs | CancerType/CancerType: ThyroidCancer |
| Projects | CancerType/CancerType: EsophagealCancer |
| Grants | CancerType/CancerType: ThyroidCancer |
| Publications | CancerType/CancerType: ThyroidCancer |

Run: `pytest Testcases/INS/result_tabs --env qa -q`

The inspected QA Explore tables expose CSV only, with no JSON menu.

## Validation observations

QA validation: all four CSV cases passed after preserving every publication/project association. Grants, Projects, and Publications sorting passed. Programs reports a Data Location Details ordering mismatch.
