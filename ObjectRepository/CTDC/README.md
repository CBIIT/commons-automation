# CTDC object repository

Playwright locators for the [CTDC Explore UI](https://github.com/CBIIT/crdc-ctdc-ui). Same pattern as C3DC: each filter group has **`facet`**, **`dropdown`**, and **`checkboxes`**.

## Layout

| Path | Contents |
|------|-----------|
| `filters/participants.yaml` | Diagnosis, Sex, Race, Ethnicity, Carcinogen Exposure, Targeted Therapy |
| `filters/biospecimens.yaml` | Anatomical Collection Site, Tissue Category, Collection Timepoint |
| `filters/files.yaml` | File Type, File Format |
| `nav_bar.yaml`, `home.yaml`, `header.yaml` | Navigation and warning banner |
| `statbar.yaml` | Six explore stats (`statsbar_count_1` … `_6`) |
| `result_tabs.yaml` | Participants / Biospecimens / Files tabs and tables |
| `static/*.yaml` | Static page copy checks |

## Filter group keys (for `select_filter`)

Examples matching Katalon test intent:

- `Participants/Sex` → `Male`, `Female`
- `Participants/Race` → `Asian`, `BlkAfrAmer`, …
- `Biospecimens/TissueCategory` → `Primary`, `Metastatic`, …
- `Files/FileFormat` → `pdf`, `vcf`

Sidebar sections use facet xpaths from `crdc-ctdc-ui` (`Filter by Participants`, `Filter by Biospecimens`, `Filter by Data Files`). Dropdowns use UI `@id` labels from `src/bento/dashTemplate.js`.

## Regenerate from Katalon + UI

```bash
python3 Tools/build_ctdc_object_repository.py
```

Sources:

- `../Commons_Automation/Object Repository/CTDC` (Katalon `.rs`)
- Facet section titles and filter labels from `../ctdc-fe-be/crdc-ctdc-ui-main/src/bento/dashTemplate.js`

A few Katalon diagnosis checkboxes used `//div[contains(text(),…)]`; the builder replaces those with standard `checkbox_Diagnosis_*` ids where the UI uses Bento checkboxes.
