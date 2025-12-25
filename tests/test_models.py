"""Tests for Pydantic models.

These tests validate the request/response models for the PDF service API.
"""

import pytest
from pydantic import ValidationError


class TestPdfRequest:
    """Tests for PdfRequest model."""

    def test_pdf_request_requires_html(self):
        """PdfRequest must have an html field - missing html should raise ValidationError."""
        from app.models import PdfRequest

        with pytest.raises(ValidationError, match="html"):
            PdfRequest()

    def test_pdf_request_accepts_html_string(self, sample_html):
        """PdfRequest accepts a valid HTML string."""
        from app.models import PdfRequest

        request = PdfRequest(html=sample_html)

        assert request.html == sample_html

    def test_pdf_request_rejects_empty_html(self):
        """PdfRequest should reject empty string for html field."""
        from app.models import PdfRequest

        with pytest.raises(ValidationError, match="html"):
            PdfRequest(html="")

    def test_pdf_request_accepts_options(self, sample_html):
        """PdfRequest can include optional PdfOptions."""
        from app.models import PdfOptions, PdfRequest

        options = PdfOptions(format="A4", landscape=True)
        request = PdfRequest(html=sample_html, options=options)

        assert request.options is not None
        assert request.options.format == "A4"
        assert request.options.landscape is True

    def test_pdf_request_options_default_none(self, sample_html):
        """PdfRequest options should default to None when not provided."""
        from app.models import PdfRequest

        request = PdfRequest(html=sample_html)

        assert request.options is None


class TestPdfOptions:
    """Tests for PdfOptions model."""

    def test_pdf_options_defaults(self):
        """PdfOptions should have sensible defaults."""
        from app.models import PdfOptions

        options = PdfOptions()

        assert options.format == "A4"
        assert options.landscape is False
        assert options.print_background is True

    def test_pdf_options_format_accepts_valid_values(self):
        """PdfOptions format accepts standard paper sizes."""
        from app.models import PdfOptions

        options_a4 = PdfOptions(format="A4")
        options_letter = PdfOptions(format="Letter")
        options_legal = PdfOptions(format="Legal")

        assert options_a4.format == "A4"
        assert options_letter.format == "Letter"
        assert options_legal.format == "Legal"

    def test_pdf_options_landscape_boolean(self):
        """PdfOptions landscape must be boolean."""
        from app.models import PdfOptions

        options_portrait = PdfOptions(landscape=False)
        options_landscape = PdfOptions(landscape=True)

        assert options_portrait.landscape is False
        assert options_landscape.landscape is True

    def test_pdf_options_margins(self):
        """PdfOptions accepts margin values."""
        from app.models import PdfOptions

        options = PdfOptions(
            margin_top="2cm",
            margin_bottom="2cm",
            margin_left="1.5cm",
            margin_right="1.5cm",
        )

        assert options.margin_top == "2cm"
        assert options.margin_bottom == "2cm"
        assert options.margin_left == "1.5cm"
        assert options.margin_right == "1.5cm"

    def test_pdf_options_scale(self):
        """PdfOptions accepts scale value between 0.1 and 2."""
        from app.models import PdfOptions

        options = PdfOptions(scale=1.5)

        assert options.scale == 1.5


class TestPdfResponse:
    """Tests for PdfResponse model."""

    def test_pdf_response_structure(self):
        """PdfResponse should have success status and optional message."""
        from app.models import PdfResponse

        response = PdfResponse(success=True, message="PDF generated")

        assert response.success is True
        assert response.message == "PDF generated"

    def test_pdf_response_success_required(self):
        """PdfResponse requires success field."""
        from app.models import PdfResponse

        with pytest.raises(ValidationError, match="success"):
            PdfResponse()

    def test_pdf_response_message_optional(self):
        """PdfResponse message should be optional."""
        from app.models import PdfResponse

        response = PdfResponse(success=True)

        assert response.success is True
        assert response.message is None

    def test_pdf_response_error_state(self):
        """PdfResponse can represent error state."""
        from app.models import PdfResponse

        response = PdfResponse(success=False, message="Failed to generate PDF")

        assert response.success is False
        assert response.message == "Failed to generate PDF"
