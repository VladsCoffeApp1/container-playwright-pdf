# Cloud Run Playwright PDF Service

A lightweight HTTP service that converts HTML to PDF using Playwright and headless Chromium. Designed for deployment on Google Cloud Run.

## API Endpoints

### POST /pdf

Convert HTML content to PDF.

**Request:**

```json
{
  "html": "<html><body><h1>Hello World</h1></body></html>",
  "options": {
    "format": "A4",
    "landscape": false,
    "print_background": true,
    "margin_top": "1cm",
    "margin_bottom": "1cm",
    "margin_left": "1cm",
    "margin_right": "1cm",
    "scale": 1.0
  }
}
```

**Response:** Binary PDF file (`application/pdf`)

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| format | string | "A4" | Paper format (A4, Letter, Legal, etc.) |
| landscape | boolean | false | Use landscape orientation |
| print_background | boolean | true | Print background graphics |
| margin_top | string | null | Top margin (e.g., "1cm", "0.5in") |
| margin_bottom | string | null | Bottom margin |
| margin_left | string | null | Left margin |
| margin_right | string | null | Right margin |
| scale | float | null | Scale factor (0.1 to 2.0) |

### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "ok",
  "service": "playwright-pdf"
}
```

## Usage Example

```bash
curl -X POST http://localhost:8080/pdf \
  -H "Content-Type: application/json" \
  -d '{"html": "<h1>Hello</h1><p>World</p>"}' \
  --output document.pdf
```

## Local Development

Start the service locally with Docker Compose:

```bash
docker-compose up --build
```

The service will be available at `http://localhost:8080`.

### Running Tests

```bash
# Install dependencies
uv sync

# Install Playwright browser
uv run playwright install chromium

# Run tests
uv run pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PDF_LOG_LEVEL | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| PDF_REQUEST_TIMEOUT | 60 | Request timeout in seconds |
| PORT | 8080 | HTTP server port (set automatically by Cloud Run) |

## Cloud Run Configuration

The service is configured for Cloud Run with the following settings:

| Setting | Value |
|---------|-------|
| Memory | 1Gi |
| CPU | 1 |
| Concurrency | 1 |
| Timeout | 60s |
| Min instances | 0 |
| Max instances | 5 |

**Note:** Concurrency is set to 1 because Chromium PDF rendering is memory-intensive. Each request gets its own browser context for isolation.

## Deployment

Deployment is automated via GitHub Actions on push to `main`. The workflow:

1. Runs tests
2. Builds Docker image
3. Pushes to Artifact Registry
4. Deploys to Cloud Run

Required GitHub secrets:
- `GCP_SA_KEY` - Service account JSON key
- `GCP_PROJECT_ID` - Google Cloud project ID

## Project Structure

```
container-playwright-pdf/
  app/
    main.py         # FastAPI application
    models.py       # Pydantic request/response models
    pdf_service.py  # Playwright PDF generation
  tests/            # Test suite
  Dockerfile        # Multi-stage Docker build
  docker-compose.yaml
  pyproject.toml    # Dependencies and config
  project.env       # Environment variables
```
