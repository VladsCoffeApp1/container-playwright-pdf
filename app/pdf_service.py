"""PDF generation service using Playwright.

This module provides the PdfService class for converting HTML to PDF
using a headless Chromium browser via Playwright.
"""

from loguru import logger as log
from playwright.async_api import Browser, Playwright, async_playwright

from app.models import PdfOptions


class PdfService:
    """Service for generating PDFs from HTML content using Playwright.

    This service manages the browser lifecycle and provides PDF generation
    capabilities. It can be injected with a mock Playwright instance for testing.

    :param playwright: Optional Playwright instance for dependency injection
    """

    def __init__(self, playwright: Playwright | None = None):
        """Initialize the PDF service.

        :param playwright: Optional Playwright instance (for testing)
        """
        self._playwright: Playwright | None = playwright
        self._browser: Browser | None = None
        self._owns_playwright: bool = playwright is None
        self._is_ready: bool = playwright is not None

    @property
    def is_ready(self) -> bool:
        """Check if the service is ready to process requests.

        :returns: True if the service has been started and is ready
        """
        return self._is_ready

    async def start(self) -> None:
        """Start the PDF service and launch the browser.

        Initializes Playwright and launches a headless Chromium browser.

        :raises RuntimeError: If the service is already started
        """
        if self._is_ready and not self._playwright:
            log.warning("PDF service already started")
            return

        log.info("Starting PDF service...")

        if self._owns_playwright:
            playwright_context = async_playwright()
            self._playwright = await playwright_context.start()

        if self._playwright:
            self._browser = await self._playwright.chromium.launch(headless=True)
            self._is_ready = True
            log.info("PDF service started successfully")

    async def stop(self) -> None:
        """Stop the PDF service and close the browser.

        Cleans up browser resources and Playwright instance.
        """
        log.info("Stopping PDF service...")

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._owns_playwright and self._playwright:
            await self._playwright.stop()
            self._playwright = None

        self._is_ready = False
        log.info("PDF service stopped")

    async def generate_pdf(self, html: str, options: PdfOptions | None = None) -> bytes:
        """Generate a PDF from HTML content.

        :param html: HTML content to convert to PDF
        :param options: Optional PDF generation options
        :returns: PDF content as bytes
        :raises RuntimeError: If the service is not started
        :raises Exception: If PDF generation fails
        """
        if not self._is_ready:
            raise RuntimeError("PDF service is not started or not ready")

        if options is None:
            options = PdfOptions()

        log.debug(f"Generating PDF with options: {options}")

        # Get browser - either injected playwright or our own
        if self._browser:
            browser = self._browser
        elif self._playwright:
            browser = await self._playwright.chromium.launch(headless=True)
        else:
            raise RuntimeError("No browser available")

        # Create a new context and page
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Set the HTML content
            await page.set_content(html, timeout=180000)

            # Wait for DOM to be loaded
            await page.wait_for_load_state("domcontentloaded", timeout=180000)

            # Build PDF options dictionary
            pdf_options = self._build_pdf_options(options)

            # Generate PDF
            pdf_bytes = await page.pdf(**pdf_options)

            log.debug(f"Generated PDF: {len(pdf_bytes)} bytes")
            return pdf_bytes

        finally:
            # Always close the page
            await page.close()
            await context.close()

    def _build_pdf_options(self, options: PdfOptions) -> dict:
        """Build Playwright PDF options dictionary from PdfOptions model.

        :param options: PdfOptions model instance
        :returns: Dictionary of options for Playwright's page.pdf()
        """
        pdf_opts: dict = {
            "format": options.format,
            "landscape": options.landscape,
            "print_background": options.print_background,
        }

        # Add margin options if specified
        margin = {}
        if options.margin_top:
            margin["top"] = options.margin_top
        if options.margin_bottom:
            margin["bottom"] = options.margin_bottom
        if options.margin_left:
            margin["left"] = options.margin_left
        if options.margin_right:
            margin["right"] = options.margin_right

        if margin:
            pdf_opts["margin"] = margin

        # Add scale if specified
        if options.scale:
            pdf_opts["scale"] = options.scale

        return pdf_opts
