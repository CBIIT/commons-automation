# Bento result tabs

Cases follow the C3DC layout: one folder per tab, TC01 for CSV and TC03 for sorting.
TC02 is reserved for JSON when the application exposes a JSON export control.

Sorting discovers enabled controls, verifies ascending/descending values across every page,
and checks exact row retention. Constant-value columns are reported as INCONCLUSIVE.
Sorting does not require a query workbook or database connection.

| Tab | Filters |
| --- | --- |
| Cases | Filter/Arm: A; Filter/Diagnosis: Adenocarcinoma |
| Samples | Filter/Arm: A; Filter/Diagnosis: Adenocarcinoma |
| Files | Filter/Arm: A; Filter/Diagnosis: Adenocarcinoma |

Run: `pytest Testcases/BENTO/result_tabs --env qa -q`

The inspected Explore tables expose sorting but no CSV/JSON download control.
Download cases are not added for absent controls.

## Validation observations

Live validation: Files and Samples sorting passed. Cases reports Recurrence Score and Tumor Size ordering mismatches; those columns remain checked.
