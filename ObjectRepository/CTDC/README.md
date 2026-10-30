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

Update YAML here when the CTDC UI changes. Facet section titles and filter labels align with `crdc-ctdc-ui` (`dashTemplate.js` filter `@id`s).
