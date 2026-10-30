"""
GC Studies listing page (/#/studies).

Catalog of all studies (navbar Studies — not Data explore).

Flow: open listing → read paginated table → StudiesListingTab Cypher → Excel → compare.
"""
from Commons import action_log, excel_writer
from Commons.compare import compare_tables
from Commons.table_reader import read_table_data

# ---------------------------------------------------------------------------
# Navigation
# ---------------------------------------------------------------------------


def open_studies_listing(app):
    """Open /studies and wait for the listing table."""
    app.click("NavBar/Studies-Listing", ui_message="Studies listing page opened successfully.")
    app.ui.wait_visible(app.repo.xpath("StudiesPage/Table"))


# ---------------------------------------------------------------------------
# Listing compare (StudiesListingTab in TC*.xlsx)
# ---------------------------------------------------------------------------


def verify_studies_listing(app):
    """Read UI table, fetch expected rows from Memgraph, write *_UI / *_DB, compare."""
    if app.query_file is None:
        raise RuntimeError("Call load_query_file() first")

    page_table = read_table_data(
        app.ui,
        app_key=app.NAME,
        table_xpath=app.repo.xpath("StudiesPage/Table"),
        header_xpath=app.repo.xpath("StudiesPage/Table-Hdr"),
        next_xpath=app.repo.xpath("StudiesPage/Next-Btn"),
        next_repo_key="StudiesPage/Next-Btn",
        max_pages=app.MAX_PAGES,
    )

    db_table = app.source.fetch_tab_table(
        app.query_file,
        "StudiesListingTab",
        tab_display_name="Studies listing",
        apply_row_limit=False,
    )

    # UI uses thousands separators; format DB counts to match (Participants, Files).
    for col_index, col_name in enumerate(db_table.header):
        if col_name not in ("Number of Participants", "Number of Files"):
            continue
        for row in db_table.rows:
            raw = str(row[col_index]).replace(",", "").strip()
            if raw.isdigit():
                row[col_index] = f"{int(raw):,}"

    page_table.rows.sort(key=lambda row: [str(c).strip() if c is not None else "" for c in row])
    db_table.rows.sort(key=lambda row: [str(c).strip() if c is not None else "" for c in row])

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
