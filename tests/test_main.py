"""Tests for FastAPI endpoints.

These tests validate the API endpoints of the PDF service.
"""

import pytest


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_returns_ok(self, test_client):
        """Health endpoint should return 200 OK with status."""
        response = test_client.get("/health")

        assert response.status_code == 200
        body = response.json()
        assert body.get("status") == "ok"

    def test_health_includes_service_name(self, test_client):
        """Health endpoint should include service name."""
        response = test_client.get("/health")

        body = response.json()
        assert "service" in body
        assert body.get("service") == "playwright-pdf"


class TestPdfEndpoint:
    """Tests for POST /pdf endpoint."""

    def test_pdf_endpoint_returns_pdf_content_type(self, test_client, pdf_request_data):
        """POST /pdf should return application/pdf content type."""
        response = test_client.post("/pdf", json=pdf_request_data)

        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"

    def test_pdf_endpoint_returns_pdf_bytes(self, test_client, pdf_request_data):
        """POST /pdf should return valid PDF bytes."""
        response = test_client.post("/pdf", json=pdf_request_data)

        assert response.status_code == 200
        # PDF files start with %PDF magic bytes
        assert response.content.startswith(b"%PDF")

    def test_pdf_endpoint_rejects_missing_html(self, test_client):
        """POST /pdf should return 422 when html is missing."""
        response = test_client.post("/pdf", json={})

        assert response.status_code == 422
        body = response.json()
        assert "detail" in body

    def test_pdf_endpoint_rejects_empty_html(self, test_client):
        """POST /pdf should return 422 for empty html string."""
        response = test_client.post("/pdf", json={"html": ""})

        assert response.status_code == 422

    def test_pdf_endpoint_accepts_options(self, test_client, pdf_request_with_options):
        """POST /pdf should accept and apply PDF options."""
        response = test_client.post("/pdf", json=pdf_request_with_options)

        assert response.status_code == 200
        assert response.headers.get("content-type") == "application/pdf"

    def test_pdf_endpoint_sets_content_disposition(self, test_client, pdf_request_data):
        """POST /pdf should set Content-Disposition header for download."""
        response = test_client.post("/pdf", json=pdf_request_data)

        assert response.status_code == 200
        content_disposition = response.headers.get("content-disposition")
        assert content_disposition is not None
        assert "attachment" in content_disposition or "inline" in content_disposition

    def test_pdf_endpoint_handles_complex_html(self, test_client, sample_html_with_styles):
        """POST /pdf should handle HTML with styles and complex content."""
        response = test_client.post("/pdf", json={"html": sample_html_with_styles})

        assert response.status_code == 200
        assert response.content.startswith(b"%PDF")


class TestPdfEndpointOptions:
    """Tests for PDF options handling in POST /pdf endpoint."""

    @pytest.mark.parametrize(
        ("format_value", "expected_status"),
        [
            pytest.param("A4", 200, id="a4_format"),
            pytest.param("Letter", 200, id="letter_format"),
            pytest.param("Legal", 200, id="legal_format"),
            pytest.param("A3", 200, id="a3_format"),
        ],
    )
    def test_pdf_endpoint_accepts_paper_formats(self, test_client, sample_html, format_value, expected_status):
        """POST /pdf should accept various paper format options."""
        payload = {"html": sample_html, "options": {"format": format_value}}

        response = test_client.post("/pdf", json=payload)

        assert response.status_code == expected_status

    def test_pdf_endpoint_accepts_landscape_option(self, test_client, sample_html):
        """POST /pdf should accept landscape orientation option."""
        payload = {"html": sample_html, "options": {"landscape": True}}

        response = test_client.post("/pdf", json=payload)

        assert response.status_code == 200

    def test_pdf_endpoint_accepts_margin_options(self, test_client, sample_html):
        """POST /pdf should accept margin options."""
        payload = {
            "html": sample_html,
            "options": {
                "margin_top": "2cm",
                "margin_bottom": "2cm",
                "margin_left": "1cm",
                "margin_right": "1cm",
            },
        }

        response = test_client.post("/pdf", json=payload)

        assert response.status_code == 200


class TestPdfEndpointErrorHandling:
    """Tests for error handling in POST /pdf endpoint."""

    def test_pdf_endpoint_returns_error_for_invalid_json(self, test_client):
        """POST /pdf should return 422 for invalid JSON body."""
        response = test_client.post(
            "/pdf",
            content="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_pdf_endpoint_returns_error_detail(self, test_client):
        """POST /pdf error response should include detail message."""
        response = test_client.post("/pdf", json={})

        assert response.status_code == 422
        body = response.json()
        assert "detail" in body
        # Detail should mention the missing field
        detail_str = str(body.get("detail"))
        assert "html" in detail_str.lower()
