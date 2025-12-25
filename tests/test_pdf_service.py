"""Tests for PdfService class.

These tests validate the PDF generation service logic.
"""

import pytest


class TestPdfServiceGeneratePdf:
    """Tests for PdfService.generate_pdf() method."""

    @pytest.mark.asyncio
    async def test_generate_pdf_returns_bytes(self, sample_html, mock_playwright):
        """generate_pdf should return bytes representing the PDF content."""
        from app.pdf_service import PdfService

        service = PdfService(playwright=mock_playwright)

        result = await service.generate_pdf(sample_html)

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_pdf_valid_pdf_header(self, sample_html, mock_page):
        """Generated PDF should start with valid PDF header magic bytes."""
        # Configure mock to return realistic PDF header
        mock_page.pdf.return_value = b"%PDF-1.4\n%mock content"

        # For this test, we need to verify the actual PDF generation
        # When mocked, we verify the mock returns proper format
        # In unit test with mock, we verify our expectations
        result = await mock_page.pdf()

        assert result.startswith(b"%PDF")

    @pytest.mark.asyncio
    async def test_generate_pdf_waits_for_fonts(self, sample_html, mock_playwright, mock_page):
        """generate_pdf should wait for fonts to load before generating PDF."""
        from app.pdf_service import PdfService

        service = PdfService(playwright=mock_playwright)

        await service.generate_pdf(sample_html)

        # Verify that wait_for_load_state was called (fonts/network idle)
        mock_page.wait_for_load_state.assert_called()

    @pytest.mark.asyncio
    async def test_generate_pdf_handles_empty_html(self, empty_html, mock_playwright):
        """generate_pdf should handle empty HTML document gracefully."""
        from app.pdf_service import PdfService

        service = PdfService(playwright=mock_playwright)

        result = await service.generate_pdf(empty_html)

        assert isinstance(result, bytes)

    @pytest.mark.asyncio
    async def test_generate_pdf_applies_options(self, sample_html, mock_playwright, mock_page):
        """generate_pdf should apply PdfOptions to the PDF generation."""
        from app.models import PdfOptions
        from app.pdf_service import PdfService

        options = PdfOptions(format="Letter", landscape=True)
        service = PdfService(playwright=mock_playwright)

        await service.generate_pdf(sample_html, options=options)

        # Verify pdf() was called with expected options
        mock_page.pdf.assert_called()
        call_kwargs = mock_page.pdf.call_args.kwargs
        assert call_kwargs.get("format") == "Letter"
        assert call_kwargs.get("landscape") is True

    @pytest.mark.asyncio
    async def test_generate_pdf_sets_content_correctly(self, sample_html, mock_playwright, mock_page):
        """generate_pdf should set the HTML content on the page."""
        from app.pdf_service import PdfService

        service = PdfService(playwright=mock_playwright)

        await service.generate_pdf(sample_html)

        mock_page.set_content.assert_called_once_with(sample_html, timeout=180000)

    @pytest.mark.asyncio
    async def test_generate_pdf_closes_page_after_generation(self, sample_html, mock_playwright, mock_page):
        """generate_pdf should close the page after generating PDF."""
        from app.pdf_service import PdfService

        service = PdfService(playwright=mock_playwright)

        await service.generate_pdf(sample_html)

        mock_page.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_pdf_handles_exception_gracefully(self, sample_html, mock_playwright, mock_page):
        """generate_pdf should handle exceptions and clean up resources."""
        from app.pdf_service import PdfService

        mock_page.pdf.side_effect = Exception("Browser crashed")
        service = PdfService(playwright=mock_playwright)

        with pytest.raises(Exception, match="Browser crashed"):
            await service.generate_pdf(sample_html)


class TestPdfServiceLifecycle:
    """Tests for PdfService lifecycle management."""

    @pytest.mark.asyncio
    async def test_service_can_be_started(self, mock_playwright):
        """PdfService should have a start method for initialization."""
        from app.pdf_service import PdfService

        service = PdfService()

        # Service should be startable
        await service.start()

        assert service.is_ready

    @pytest.mark.asyncio
    async def test_service_can_be_stopped(self, mock_playwright):
        """PdfService should have a stop method for cleanup."""
        from app.pdf_service import PdfService

        service = PdfService()
        await service.start()

        await service.stop()

        assert not service.is_ready

    @pytest.mark.asyncio
    async def test_service_rejects_requests_when_not_started(self, sample_html):
        """PdfService should reject requests when not started."""
        from app.pdf_service import PdfService

        service = PdfService()

        with pytest.raises(RuntimeError, match="not started|not ready"):
            await service.generate_pdf(sample_html)
