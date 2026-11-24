"""C3DC home-page navigation and static-content checks."""


def open_home_page(app):
    """Open the home page in the configured environment."""
    app.goto('/')


def verify_home_page_content(app):
    """Compare text and links with the HomePage sheet of C3DC_StaticData.xlsx."""
    app.verify_static_data('HomePage')
