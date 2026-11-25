# ICDC result tabs

Cases follow the C3DC layout: one folder per tab, TC01 for CSV and TC03 for sorting.
TC02 is reserved for JSON when the application exposes a JSON export control.

Sorting discovers enabled controls, verifies ascending/descending values across every page,
and checks exact row retention. Constant-value columns are reported as INCONCLUSIVE.
Sorting does not require a query workbook or database connection.

CSV cases load `InputFiles/ICDC/ICDC_ResultTabDownloads.xlsx`.
Each tab has a full export projection followed by a separate count query. Both bypass
display row limits. Verification requires every exported column and exact record membership;
it does not treat a successful download or matching row count as content validation.

Controls: `ObjectRepository/ICDC/result_tabs/<tab>.yaml`.
Export schemas: `Commons/apps/icdc/result_tabs.py`.

| Tab | Filters |
| --- | --- |
| Cases | Cases/Study: Canine_Filter_Study-COTC021; Cases/Breed: BernMtnDog |
| Samples | Cases/Study: Canine_Filter_Study-COTC021; Cases/Breed: BernMtnDog |
| Case Files | Cases/Study: Canine_Filter_Study-COTC021; Cases/Breed: BernMtnDog |
| Study Files | Cases/Study: Canine_Filter_Study-COTC021; Cases/Breed: BernMtnDog |

Run: `pytest Testcases/ICDC/result_tabs --env qa -q`

The inspected QA Explore tables expose CSV only, with no JSON menu.

## Validation observations

Earlier QA validation: all four CSV cases passed, as did Cases, Samples, and Study Files sorting. The earlier Case Files Sample ID failure is unconfirmed pending a synchronization-aware rerun.

Case Files sorting now waits for the response matching the requested column, direction, first page, and case-file scope, then waits for the returned file names to render before validating order. Sorting and row-retention assertions remain enabled. The targeted unit run passed 51 tests, including a delayed-render regression. Live revalidation could not reach sorting because a fresh QA Explore session did not render its filters or tables, including after a 90-second wait for the Study filter.
