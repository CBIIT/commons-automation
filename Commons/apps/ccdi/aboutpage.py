"""About page content verification for the CCDI Hub."""


class AboutPage:
    """Expose About page Excel actions using the CCDI app context."""

    # --- About page verification ---

    def verify_about_page_data(self):
        """Verify About content against the shared workbook's AboutPage sheet.

        The testcase accepts the banner and navigates through the About menu.
        The shared verifier prints expected/actual text and link URLs, records
        every mismatch, and writes the AboutPage output sheet.
        """
        self.verify_static_data("AboutPage")
