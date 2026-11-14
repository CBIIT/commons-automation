# PSDC locators

Inspected on QA at https://populationsciences-qa.datacommons.cancer.gov/#/.

- `Home`, `NavBar`: banner and navigation.
- `Statbar`: all six displayed metrics. Data Volume is available for UI checks.
- `ResultTabs`: the Explore Studies grid and pagination. PSDC does not expose
  Participants or Files result tabs on Explore.
- `Filters/Studies`, `Filters/Participants`: checkbox IDs observed on QA.
  Numeric/range filters need dedicated interaction support before use.
- `StudyDetails`: seven detail navigation tabs, study-file and personnel tables.
- `Static/AboutPage`, `Static/AccessDataPage`, `Static/AnalyzeDataPage`,
  `Static/SupportPage`: headings, body paragraphs, and outbound links.
  About-menu IDs are scoped to the desktop wrapper to exclude hidden mobile
  duplicates; page content is scoped to `main` and uses no generated classes.
- `Static/HomePage`: welcome banner, content-panel text and links, and static
  footer content. Footer controls are scoped to the desktop wrapper to exclude
  hidden mobile copies. Tile locators use the page's stable `tile*_...` IDs.

The Studies grid has no stable table ID. Its locator uses the `study_short_name`
column class to avoid generated Material UI class names and positional tables.
Numeric stat IDs start with **Data Volume** at position 1, so Studies is 2.
