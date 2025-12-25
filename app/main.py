"""FastAPI application for HTML-to-PDF conversion service.

This module provides REST API endpoints for converting HTML to PDF
using Playwright/Chromium.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from playwright.async_api import TimeoutError as PlaywrightTimeout
from loguru import logger as log

from app.models import PdfRequest
from app.pdf_service import PdfService

# Global PDF service instance
pdf_service: PdfService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle - start/stop PdfService.

    :param app: FastAPI application instance
    :yields: None
    """
    global pdf_service
    log.info("Starting PDF service...")
    pdf_service = PdfService()
    await pdf_service.start()
    log.info("PDF service started successfully")

    yield

    log.info("Stopping PDF service...")
    if pdf_service:
        await pdf_service.stop()
    log.info("PDF service stopped")


app = FastAPI(
    title="playwright-pdf",
    description="HTML to PDF conversion service using Playwright",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint.

    :returns: Health status with service info
    """
    return {
        "status": "ok",
        "service": "playwright-pdf",
    }


@app.post("/pdf")
async def generate_pdf(request: PdfRequest) -> Response:
    """Generate PDF from HTML content.

    :param request: PDF generation request with HTML and options
    :returns: PDF file as binary response
    :raises HTTPException: If PDF generation fails
    """
    if pdf_service is None:
        raise RuntimeError("PDF service not initialized")

    try:
        pdf_bytes = await pdf_service.generate_pdf(
            html=request.html,
            options=request.options,
        )
    except PlaywrightTimeout:
        raise HTTPException(
            status_code=504,
            detail="PDF generation timed out - HTML too large or complex"
        )
    except Exception as e:
        log.error(f"PDF generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "inline; filename=document.pdf",
        },
    )
