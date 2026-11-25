# GC result tabs

Cases follow the C3DC layout: one folder per tab, TC01 for CSV and TC03 for sorting.
TC02 is reserved for JSON when the application exposes a JSON export control.

Sorting discovers enabled controls, verifies ascending/descending values across every page,
and checks exact row retention. Constant-value columns are reported as INCONCLUSIVE.
Sorting does not require a query workbook or database connection.

| Tab | Filters |
| --- | --- |
| Participants | StudyFacet/PHS_Accession: phs000720; FilesFacet/FileType: hdf5 |
| Samples | StudyFacet/PHS_Accession: phs000720; FilesFacet/FileType: hdf5 |
| Files | StudyFacet/PHS_Accession: phs000720; FilesFacet/FileType: hdf5 |

Run: `pytest Testcases/GC/result_tabs --env qa2 -q`

CSV cases load `InputFiles/GC/GC_ResultTabDownloads.xlsx`. Its `Queries` sheet groups
an export projection and a separate count query for each tab. The `Parameters`
sheet supplies `study`, `file_type`, and the export safety `limit`. Queries bind these
parameters through the existing Memgraph source and bypass display row limits.
Independent counts reject truncated expected data.

The projections follow `.cursor/skills/gc-cypher-assistant/backend-index-query/indices.yaml`
and the GC model references. Every exported column is compared against Memgraph,
including complete related-file/sample metadata. Array comparisons preserve full
labels containing commas and duplicate values while allowing unspecified array order.

Controls live in `ObjectRepository/GC/result_tabs/<tab>.yaml`; the CSV adapter and
rendering specifications live in `Commons/apps/gc/result_tabs.py`.

The UI inspected on QA and QA2 exposes CSV only, with no JSON menu.

## Validation observations

QA2 validation: all three CSV cases passed, with 20 complete records per export matched against Memgraph and independent counts. Files and Samples sorting passed. Participants sorting reports that the Samples column values do not follow the requested order. Both directions were also checked directly against the live table.
