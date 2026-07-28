"""
Application constants.

Shared constants used across the Auction Intelligence API.
"""

from __future__ import annotations

# ==========================================================
# Application
# ==========================================================

APP_NAME = "Auction Intelligence API"

APP_VERSION = "1.0.0"


# ==========================================================
# Upload Status
# ==========================================================

UPLOAD_PENDING = "PENDING"

UPLOAD_UPLOADED = "UPLOADED"

UPLOAD_PROCESSING = "PROCESSING"

UPLOAD_COMPLETED = "COMPLETED"

UPLOAD_FAILED = "FAILED"


# ==========================================================
# OCR
# ==========================================================

DEFAULT_LANGUAGE = "en"

MINIMUM_OCR_CONFIDENCE = 0.50


# ==========================================================
# AI Confidence
# ==========================================================

MINIMUM_EXTRACTION_CONFIDENCE = 0.75


# ==========================================================
# Supported File Types
# ==========================================================

IMAGE_EXTENSIONS = (

    ".jpg",

    ".jpeg",

    ".png",

    ".tif",

    ".tiff",

)

SUPPORTED_EXTENSIONS = (

    *IMAGE_EXTENSIONS,

    ".pdf",

)


# ==========================================================
# MIME Types
# ==========================================================

SUPPORTED_CONTENT_TYPES = (

    "image/jpeg",

    "image/png",

    "image/tiff",

)


# ==========================================================
# Image Processing
# ==========================================================

MAX_IMAGE_WIDTH = 3000

MAX_IMAGE_HEIGHT = 3000

JPEG_QUALITY = 95


# ==========================================================
# Currency
# ==========================================================

DEFAULT_CURRENCY = "INR"


# ==========================================================
# Date Formats
# ==========================================================

DATE_FORMAT = "%d-%m-%Y"

DATETIME_FORMAT = "%d-%m-%Y %H:%M:%S"


# ==========================================================
# Database
# ==========================================================

DEFAULT_PAGE_SIZE = 20

MAX_PAGE_SIZE = 100


# ==========================================================
# Auction Types
# ==========================================================

AUCTION_TYPES = (

    "E-Auction",

    "Physical Auction",

    "Online Auction",

)


# ==========================================================
# Asset Categories
# ==========================================================

ASSET_CATEGORIES = (

    "Residential",

    "Commercial",

    "Industrial",

    "Agricultural",

    "Vehicle",

    "Machinery",

    "Land",

    "Apartment",

    "House",

    "Flat",

    "Plot",

    "Others",

)


# ==========================================================
# Bank Keywords
# ==========================================================

BANK_KEYWORDS = (

    "State Bank of India",

    "Indian Bank",

    "Canara Bank",

    "Punjab National Bank",

    "Union Bank of India",

    "Bank of Baroda",

    "Bank of India",

    "Central Bank of India",

    "UCO Bank",

    "Indian Overseas Bank",

    "Axis Bank",

    "ICICI Bank",

    "HDFC Bank",

)


# ==========================================================
# Regex Patterns
# ==========================================================

IFSC_PATTERN = r"[A-Z]{4}0[A-Z0-9]{6}"

PAN_PATTERN = r"[A-Z]{5}[0-9]{4}[A-Z]"

PINCODE_PATTERN = r"\b\d{6}\b"

PHONE_PATTERN = r"(?:\+91[- ]?)?[6-9]\d{9}"


# ==========================================================
# Processing Pipeline
# ==========================================================

PIPELINE_STEPS = (

    "Upload",

    "Image Enhancement",

    "Deskew",

    "Layout Detection",

    "Auction Splitting",

    "OCR",

    "Regex Extraction",

    "LLM Extraction",

    "Validation",

    "Field Mapping",

    "Confidence Scoring",

    "Database Storage",

)


# ==========================================================
# API Messages
# ==========================================================

SUCCESS = "Success"

FAILED = "Failed"

PROCESS_STARTED = "Processing started."

PROCESS_COMPLETED = "Processing completed."

PROCESS_FAILED = "Processing failed."

UPLOAD_SUCCESS = "File uploaded successfully."

UPLOAD_FAILED_MESSAGE = "File upload failed."

DATABASE_SUCCESS = "Data stored successfully."

DATABASE_FAILED = "Database operation failed."