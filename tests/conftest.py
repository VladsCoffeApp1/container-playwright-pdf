"""Pytest fixtures for PDF service tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """FastAPI test client fixture.

    Note: Import inside fixture to allow tests to run even when
    app module doesn't exist yet (TDD approach).

    Uses context manager to properly execute lifespan events.
    """
    from app.main import app

    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_html():
    """Sample HTML content for testing."""
    return "<html><body><h1>Test Document</h1><p>This is a test.</p></body></html>"


@pytest.fixture
def sample_html_with_styles():
    """Sample HTML with CSS styles for testing."""
    return """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            h1 { color: navy; }
        </style>
    </head>
    <body>
        <h1>Styled Document</h1>
        <p>This document has styles.</p>
    </body>
    </html>
    """


@pytest.fixture
def empty_html():
    """Empty HTML document for edge case testing."""
    return "<html><body></body></html>"


@pytest.fixture
def mock_page():
    """Mock Playwright page object."""
    page = AsyncMock()
    page.set_content = AsyncMock()
    page.pdf = AsyncMock(return_value=b"%PDF-1.4 mock pdf content")
    page.wait_for_load_state = AsyncMock()
    page.close = AsyncMock()
    return page


@pytest.fixture
def mock_browser_context(mock_page):
    """Mock Playwright browser context."""
    context = AsyncMock()
    context.new_page = AsyncMock(return_value=mock_page)
    context.close = AsyncMock()
    return context


@pytest.fixture
def mock_browser(mock_browser_context):
    """Mock Playwright browser for unit tests.

    This fixture allows testing PDF generation logic without
    actually launching a browser.
    """
    browser = AsyncMock()
    browser.new_context = AsyncMock(return_value=mock_browser_context)
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_playwright(mock_browser):
    """Mock Playwright instance."""
    playwright = MagicMock()
    playwright.chromium = MagicMock()
    playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    return playwright


@pytest.fixture
def pdf_request_data(sample_html):
    """Valid PDF request payload."""
    return {"html": sample_html}


@pytest.fixture
def pdf_request_with_options(sample_html):
    """PDF request with custom options."""
    return {
        "html": sample_html,
        "options": {
            "format": "A4",
            "landscape": False,
            "margin_top": "1cm",
            "margin_bottom": "1cm",
            "margin_left": "1cm",
            "margin_right": "1cm",
        },
    }
