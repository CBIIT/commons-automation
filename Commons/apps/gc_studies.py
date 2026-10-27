"""
GC Studies listing page (/#/studies).

This is the catalog of all studies (the Studies link in the top nav).
It is not the Data explore page.

Steps:
  1. Click Studies
  2. Read the table from the page
  3. Run the Cypher query from the Excel file
  4. Sort both tables the same way, then save Excel
  5. Compare the two
"""
from Commons import action_log, excel_writer
from Commons.compare import compare_tables
from Commons.table_reader import read_table_data


def open_studies_listing(app):
    """Open the Studies catalog page.

    Clicks the Studies link in the top navbar (not Data explore) and waits
    until the studies table is visible.
    """
    app.click("NavBar/Studies-Listing", ui_message="Studies listing page opened successfully.")
    app.ui.wait_visible(app.repo.xpath("StudiesPage/Table"))


def verify_studies_listing(app):
    """Check that every study on the page matches the database.

    Reads the table from the page, runs the StudiesListingTab query from the
    Excel file, then compares the two. If a row fails, open the saved
    UI_StudiesListing and DB_StudiesListing Excel files in the Reports folder.
    """
    if app.query_file is None:
        raise RuntimeError("Call load_query_file() first")

    # 1. Read every study on the page (clicks Next until the last page).
    #    Do not use tab_row_limit — that cap is only for Data explore tabs.
    page_table = read_table_data(
        app.ui,
        app_key=app.NAME,
        table_xpath=app.repo.xpath("StudiesPage/Table"),
        header_xpath=app.repo.xpath("StudiesPage/Table-Hdr"),
        next_xpath=app.repo.xpath("StudiesPage/Next-Btn"),
        next_repo_key="StudiesPage/Next-Btn",
        max_pages=app.MAX_PAGES,
    )

    # 2. Run StudiesListingTab from the Excel file (all studies, no row cap)
    db_table = app.source.fetch_tab_table(
        app.query_file,
        "StudiesListingTab",
        tab_display_name="Studies listing",
        apply_row_limit=False,
    )

    # The page shows 5,256. The database returns 5256. Add commas so they match.
    for col_index, col_name in enumerate(db_table.header):
        if col_name not in ("Number of Participants", "Number of Files"):
            continue
        for row in db_table.rows:
            raw = str(row[col_index]).replace(",", "").strip()
            if raw.isdigit():
                row[col_index] = f"{int(raw):,}"

    # 3. Sort both tables the same way so the Excel files line up row-for-row
    page_table.rows.sort(key=lambda row: [str(c).strip() if c is not None else "" for c in row])
    db_table.rows.sort(key=lambda row: [str(c).strip() if c is not None else "" for c in row])

    # 4. Save both sides to Excel (open these if a row fails)
    out = app.output_dir / app.query_file.name
    excel_writer.write_sheet(
        out.with_name(out.name + "_UI.xlsx"),
        "UI_StudiesListing",
        page_table.header,
        page_table.rows,
        header_color=excel_writer.LISTING_HEADER_COLOR,
    )
    excel_writer.write_sheet(
        out.with_name(out.name + "_DB.xlsx"),
        "DB_StudiesListing",
        db_table.header,
        db_table.rows,
        header_color=excel_writer.LISTING_HEADER_COLOR,
    )

    # 5. Compare page rows to database rows
    action_log.compare_step("UI_StudiesListing", "DB_StudiesListing")
    result = compare_tables(
        page_table.rows, db_table.rows, page_table.header, db_table.header
    )
    app._record(
        "StudiesListing",
        result,
        ui_count=len(page_table.rows),
        exp_count=len(db_table.rows),
    )
