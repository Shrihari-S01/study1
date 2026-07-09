"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import AnyHttpUrl, BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict



def _csv_to_list(value: str | list[str]) -> list[str]:
    """Convert comma-separated env values into a list."""
    if isinstance(value, list):
        return value
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseSettings):
    """Runtime settings for the Auction AI API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "Auction AI"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "local"
    DEBUG: bool = True

    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    DATABASE_URL: str
    DATABASE_ECHO: bool = False
    
    

    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_BASE_URL: AnyHttpUrl = "https://api.groq.com/openai/v1"
    GROQ_TIMEOUT_SECONDS: int = 60

    OCR_LANG: str = "en"
    OCR_USE_GPU: bool = False

    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    UPLOAD_DIR: Path | None = None
    PROCESSED_DIR: Path | None = None
    WORD_OUTPUT_DIR: Path | None = None
    EXCEL_OUTPUT_DIR: Path | None = None
    TEMPLATE_DIR: Path | None = None

    MAX_UPLOAD_SIZE_MB: int = 25

    @property
    def cors_origins(self) -> list[str]:
     """Return CORS origins parsed from comma-separated env text."""
     return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def upload_dir(self) -> Path:
        return self.UPLOAD_DIR or self.BASE_DIR / "app" / "uploads"

    @property
    def processed_dir(self) -> Path:
        return self.PROCESSED_DIR or self.BASE_DIR / "app" / "uploads" / "processed"

    @property
    def word_output_dir(self) -> Path:
        return self.WORD_OUTPUT_DIR or self.BASE_DIR / "app" / "outputs" / "words"

    @property
    def excel_output_dir(self) -> Path:
        return self.EXCEL_OUTPUT_DIR or self.BASE_DIR / "app" / "outputs" / "excels"

    @property
    def template_dir(self) -> Path:
        return self.TEMPLATE_DIR or self.BASE_DIR / "app" / "templates"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings."""
    return Settings()
