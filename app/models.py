"""Pydantic models for the PDF service API.

This module defines the request/response models for HTML-to-PDF conversion.
"""

from pydantic import BaseModel, Field, field_validator


class PdfOptions(BaseModel):
    """Options for PDF generation.

    :param format: Paper format (A4, Letter, Legal, etc.)
    :param landscape: Whether to use landscape orientation
    :param print_background: Whether to print background graphics
    :param margin_top: Top margin (e.g., "1cm", "0.5in")
    :param margin_bottom: Bottom margin
    :param margin_left: Left margin
    :param margin_right: Right margin
    :param scale: Scale of the webpage rendering (0.1 to 2)
    """

    format: str = "A4"
    landscape: bool = False
    print_background: bool = True
    margin_top: str | None = None
    margin_bottom: str | None = None
    margin_left: str | None = None
    margin_right: str | None = None
    scale: float | None = None


class PdfRequest(BaseModel):
    """Request model for PDF generation.

    :param html: HTML content to convert to PDF (required, non-empty)
    :param options: Optional PDF generation options
    """

    html: str = Field(..., min_length=1)
    options: PdfOptions | None = None

    @field_validator("html")
    @classmethod
    def html_must_not_be_empty(cls, v: str) -> str:
        """Validate that html is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("html field cannot be empty")
        return v


class PdfResponse(BaseModel):
    """Response model for PDF generation.

    :param success: Whether the PDF generation was successful
    :param message: Optional message with details
    """

    success: bool
    message: str | None = None
