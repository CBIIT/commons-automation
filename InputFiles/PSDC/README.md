# PSDC expected data

PSDC follows CTDC's TSV → SQLite → Excel SQL comparison flow. Put **approved**
loading files in dated study folders:

```text
InputFiles/PSDC/
  NLST/2026-11-13/
    study.tsv
    participant.tsv
    data_collection.tsv
    study_country.tsv
    study_state_province_territory.tsv
    study_personnel.tsv
    publication.tsv
    associated_link.tsv
    file.tsv
```

Use the actual data release date for the folder name. PBCS and PLCO use the same
structure. `PSDC_TSV_ROOT` overrides this root. Original loading-template names,
`.tsv.txt` names, and tab-delimited `.txt` files are accepted. Transfer manifests
are recognized as `file` data. Files may be nested inside a release folder.

The existing NLST, PBCS, and PLCO ZIPs are staging archives. They are **not**
automatically extracted or merged: PLCO includes multiple participant exports and
superseded manifests. Select the authoritative versions before placing them in a
dated folder. Do not put earlier and final exports of the same records in one
release; overlapping records produce an error.

The prepared `2026-11-13` folders record a snapshot preparation date, not an
asserted source release date. Their `source_manifest.json` files record selected
archive members, original encodings, checksums, and excluded earlier versions:

- **NLST:** the participant file named `non-case controls (46802) plus lung
  cancer cases (2058)`, its loading-template files, and its 17-row study-file
  manifest.
- **PBCS:** its loading-template files and one-row study-file manifest.
- **PLCO:** `PLCO_participant_data_20260305_final_151383_records.txt`, its
  loading-template files, and the current first/second study-file manifests
  containing 8 and 24 files. The earlier 153,786-participant export and all
  `Superseded or Deprecated` / `Superseded or Depracated` manifests are excluded.
  The two current file parts are stored as `file_part_1.tsv` and `file_part_2.tsv`.

The unfiltered all-study testcase needs all three prepared folders. Extracted
study folders remain ignored by Git; keep the original ZIP archives and input
workbooks. Source text is retained and decoded to UTF-8 where necessary.

| Node | SQL table | Record key |
|---|---|---|
| study | df_study | study_short_name |
| participant | df_participant | participant_id |
| data_collection | df_data_collection | data_collection_record_id |
| study_country | df_study_country | study_country_record_id |
| study_state_province_territory | df_study_state_province_territory | study_state_record_id |
| study_personnel | df_study_personnel | study_personnel_record_id |
| publication | df_publication | publication_record_id |
| associated_link | df_associated_link | associated_link_record_id |
| file | df_file | data_file_name |

Later releases update matching records and append new records, as in CTDC;
omitting a record from a later release does not delete it. Child records are
identified by study **and** record key so IDs or filenames shared by studies do
not overwrite each other. Original column names and string IDs are preserved.
Leading/trailing header spaces are removed. A missing study relationship (as in
the NLST participant export) is filled from the study folder name.

SQL joins reference dotted headers with double quotes, for example:

```sql
SELECT s.study_short_name, COUNT(p.participant_id) AS participants
FROM df_study s
JOIN df_participant p ON p."study.study_short_name" = s.study_short_name
GROUP BY s.study_short_name
ORDER BY s.study_short_name;
```

Do not derive expected values from the live UI. The supplied manifests lack file
sizes, so Data Volume has a UI locator but is not included in the numeric stat
comparison. File-size/format checks need an authoritative metadata export.
