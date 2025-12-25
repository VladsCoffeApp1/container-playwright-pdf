"""Configuration settings for the PDF service.

This module uses pydantic-settings for environment-based configuration.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    :param app_name: Name of the application
    :param debug: Enable debug mode
    :param port: Port to run the service on
    :param browser_timeout: Timeout for browser operations in milliseconds
    :param max_content_length: Maximum allowed HTML content length in bytes
    """

    app_name: str = "container-playwright-pdf"
    debug: bool = False
    port: int = 8080
    browser_timeout: int = 30000
    max_content_length: int = 10 * 1024 * 1024  # 10MB

    model_config = {"env_prefix": "PDF_"}


settings = Settings()
