"""
Application Configuration.

Loads all application settings
from environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

BASE_DIR = Path(__file__).resolve().parents[2]

APP_DIR = BASE_DIR / "app"

UPLOAD_DIR = BASE_DIR / "uploads"

LOG_DIR = BASE_DIR / "logs"

MODEL_DIR = BASE_DIR / "models"

TEMP_DIR = BASE_DIR / "temp"

class Settings(BaseSettings):
    """
    Application settings.
    """

    model_config = SettingsConfigDict(

        env_file=".env",

        env_file_encoding="utf-8",

        case_sensitive=False,

        extra="ignore",

    )

    app_name: str = "Auction AI"

    app_version: str = "1.0.0"

    app_description: str = (

        "AI Powered Newspaper Auction Extraction"

    )

    environment: str = "development"

    debug: bool = True

    reload: bool = True

    api_prefix: str = "/api/v1"

    secret_key: str = Field(

        default="auction-ai-secret",

    )

    host: str = "0.0.0.0"

    port: int = 8000

    workers: int = 1

    timeout: int = 120

    php_insert_api_url: str = Field(
        default="",
        description="Loaded dynamically from .env PHP_INSERT_API_URL",
    )

    php_api_timeout: float = 30.0

    php_api_max_retries: int = 3

    file_url_base_prefix: str = Field(
        default="",
        description="Loaded dynamically from .env FILE_URL_BASE_PREFIX",
    )

    max_upload_size_mb: int = 50

    log_level: str = "INFO"

    log_format: str = (

        "%(asctime)s | %(levelname)s | %(message)s"

    )

    log_file: str = "auction_ai.log"

    docs_url: str = "/docs"

    redoc_url: str = "/redoc"

    openapi_url: str = "/openapi.json"

    mysql_host: str = Field(
        default="localhost",
    )

    mysql_port: int = 3306

    mysql_user: str = Field(
        default="root",
    )

    mysql_password: str = Field(
        default="root",
    )

    mysql_database: str = Field(
        default="auction_ai",
    )

    database_echo: bool = False

    database_pool_size: int = 10

    database_max_overflow: int = 20

    database_pool_timeout: int = 30

    gemini_api_key: str = Field(
        default="",
    )

    gemini_model: str = (
        "gemini-flash-latest"
    )

    openai_api_key: str = Field(
        default="",
    )

    openai_model: str = "gpt-4.1-mini"

    llm_provider: str = "openai"

    paddle_language: str = "en"

    use_gpu: bool = False

    use_angle_cls: bool = True

    use_space_char: bool = True

    

    ocr_confidence_threshold: float = 0.50

    max_upload_size_mb: int = 50

    max_upload_size: int = (
        50 * 1024 * 1024
    )

    allowed_extensions: tuple[str, ...] = (

        ".jpg",

        ".jpeg",

        ".png",

        ".bmp",

        ".tif",
        ".tiff",
    )

    save_original_image: bool = True

    overwrite_existing: bool = False

    max_image_width: int = 3000

    max_image_height: int = 3000

    jpeg_quality: int = 95

    image_dpi: int = 300

    deskew_enabled: bool = True

    denoise_enabled: bool = True

    enhance_enabled: bool = True

    enable_layout_detection: bool = True

    enable_auction_split: bool = True

    enable_regex: bool = True

    enable_llm: bool = True

    enable_validator: bool = True

    enable_database_save: bool = True

    enable_confidence: bool = True

    minimum_confidence: float = 0.75

    regex_weight: float = 0.70

    llm_weight: float = 0.30

    delete_temp_files: bool = True

    cleanup_after_processing: bool = True

    keep_split_images: bool = False

    enable_disk_cache: bool = False

    batch_size: int = 10

    max_auction_notices: int = 100

    processing_timeout: int = 600

    base_dir: Path = BASE_DIR

    app_dir: Path = APP_DIR

    upload_dir: Path = UPLOAD_DIR

    original_dir: Path = UPLOAD_DIR / "original"

    processed_dir: Path = UPLOAD_DIR / "processed"

    split_dir: Path = UPLOAD_DIR / "split"

    temp_dir: Path = TEMP_DIR

    log_dir: Path = LOG_DIR

    model_dir: Path = MODEL_DIR

    cors_origins: list[str] = [

        "*",

    ]

    cors_methods: list[str] = [

        "*",

    ]

    cors_headers: list[str] = [

        "*",

    ]

    cors_credentials: bool = True

    @property
    def database_url(
        self,
    ) -> str:
        """
        SQLAlchemy database URL.
        """

        return (

            "mysql+asyncmy://"

            f"{self.mysql_user}:"

            f"{self.mysql_password}@"

            f"{self.mysql_host}:"

            f"{self.mysql_port}/"

            f"{self.mysql_database}"

        )
    
    @property
    def sync_database_url(
        self,
    ) -> str:
        """
        SQLAlchemy synchronous URL.
        """

        return (

            "mysql+pymysql://"

            f"{self.mysql_user}:"

            f"{self.mysql_password}@"

            f"{self.mysql_host}:"

            f"{self.mysql_port}/"

            f"{self.mysql_database}"

        )
    

    def create_directories(
        self,
    ) -> None:
        """
        Create required directories.
        """

        directories = [

            self.upload_dir,

            self.original_dir,

            self.processed_dir,

            self.split_dir,

            self.temp_dir,

            self.log_dir,

            self.model_dir,

        ]

        for directory in directories:

            directory.mkdir(

                parents=True,

                exist_ok=True,

            )

    def info(
        self,
    ) -> dict:
        """
        Return configuration summary.
        """

        return {

            "application": self.app_name,

            "version": self.app_version,

            "environment": self.environment,

            "database": self.mysql_database,

            "gemini_model": self.gemini_model,

            "openai_model": self.openai_model,

            "llm_provider": self.llm_provider,

            "debug": self.debug,

        }
    

    def health_check(
        self,
    ) -> dict:
        """
        Configuration health.
        """

        return {

            "status": "Healthy",

            "environment": self.environment,

            "database": self.mysql_database,

            "upload_directory": str(

                self.upload_dir,

            ),

            "log_directory": str(

                self.log_dir,

            ),

        }
    

@lru_cache
def get_settings() -> Settings:
    """
    Return cached settings instance.
    """

    settings = Settings()

    settings.create_directories()

    return settings

settings = get_settings()