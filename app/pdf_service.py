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
            # Large viewport so content isn't constrained
            await page.set_viewport_size({"width": 3000, "height": 3000})

            # Set the HTML content
            await page.set_content(html, wait_until="networkidle", timeout=180000)

            # Get the exact content bounds
            dimensions = await page.evaluate("""
                () => {
                    const container = document.querySelector('.export-container');
                    if (container) {
                        return {
                            width: container.offsetWidth,
                            height: container.offsetHeight
                        };
                    }
                    // Fallback: measure actual content
                    const body = document.body;
                    return {
                        width: body.scrollWidth,
                        height: body.scrollHeight
                    };
                }
            """)

            page_width = dimensions['width']
            page_height = dimensions['height']

            log.debug(f"Content size: {page_width}x{page_height}")

            # Force container to origin, remove all spacing
            await page.add_style_tag(content="""
                html, body {
                    margin: 0 !important;
                    padding: 0 !important;
                    width: auto !important;
                    height: auto !important;
                }
                .export-container {
                    position: absolute !important;
                    top: 0 !important;
                    left: 0 !important;
                    margin: 0 !important;
                }
            """)

            # Set viewport to exact content size
            await page.set_viewport_size({"width": page_width, "height": page_height})

            # Wait for fonts
            await page.evaluate(
                "() => (document.fonts && document.fonts.ready) ? document.fonts.ready : Promise.resolve()"
            )

            # Generate PDF with exact content dimensions
            pdf_bytes = await page.pdf(
                width=f"{page_width}px",
                height=f"{page_height}px",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )

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
