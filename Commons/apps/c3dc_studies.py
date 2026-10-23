"""C3DC /studies catalog listing — not the Explore Participants Studies result tab."""
from Commons import action_log, excel_writer
from Commons.compare import compare_tables
from Commons.table_reader import read_table_data

LISTING_TAB_KEY = "StudiesListingTab"
LISTING_CHECK = "StudiesListing"
LISTING_UI_SHEET = "UI_StudiesListing"
LISTING_DB_SHEET = "DB_StudiesListing"


def open_studies_listing(app) -> None:
    """Open the /studies catalog via the navbar (not Explore → Studies)."""
    action_log.say("open_studies_listing (Navbar/Studies-Listing)")
    app.click("Navbar/Studies-Listing", ui_message="Studies listing page opened successfully.")
    app.ui.wait_visible(app.repo.xpath("StudiesPage/Table"))


def verify_studies_listing(app) -> None:
    """Read the catalog table, run StudiesListingTab Cypher, compare. Does not use verify_tab."""
    if app.query_file is None:
        raise RuntimeError("Call load_query_file() first")
    ui_table = read_table_data(
        app.ui,
        app_key=app.NAME,
        table_xpath=app.repo.xpath("StudiesPage/Table"),
        header_xpath=app.repo.xpath("StudiesPage/Table-Hdr"),
        next_xpath=app.repo.xpath("StudiesPage/Next-Btn"),
        next_repo_key="StudiesPage/Next-Btn",
        max_pages=app.settings.pagination_max_pages or app.MAX_PAGES,
        max_rows=app.settings.tab_row_limit if app.settings.tab_row_limit > 0 else None,
    )
    expected = app.source.fetch_tab_table(
        app.query_file, LISTING_TAB_KEY, tab_display_name="Studies listing"
    )
    base = app.output_dir / app.query_file.name
    excel_writer.write_sheet(
        base.with_name(base.name + "_UI.xlsx"), LISTING_UI_SHEET, ui_table.header, ui_table.rows
    )
    excel_writer.write_sheet(
        base.with_name(base.name + "_DB.xlsx"), LISTING_DB_SHEET, expected.header, expected.rows
    )
    action_log.compare_step(LISTING_UI_SHEET, LISTING_DB_SHEET)
    cmp = compare_tables(ui_table.rows, expected.rows, ui_table.header, expected.header)
    app._record(LISTING_CHECK, cmp, ui_count=len(ui_table.rows), exp_count=len(expected.rows))
