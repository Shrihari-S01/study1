"""
Application custom exceptions.

All custom exceptions inherit from AuctionAIException.
"""

from __future__ import annotations

from typing import Any


# ==========================================================
# Base Exception
# ==========================================================

class AuctionAIException(Exception):
    """
    Base exception for the Auction Intelligence API.
    """

    def __init__(
        self,
        message: str = "Application Error",
        status_code: int = 500,
        details: Any | None = None,
    ) -> None:

        self.message = message

        self.status_code = status_code

        self.details = details

        super().__init__(message)

    def to_dict(
        self,
    ) -> dict:
        """
        Convert exception to JSON response.
        """

        return {

            "success": False,

            "message": self.message,

            "status_code": self.status_code,

            "details": self.details,

        }


# ==========================================================
# Validation Exceptions
# ==========================================================

class ValidationException(AuctionAIException):
    """
    Raised when validation fails.
    """

    def __init__(
        self,
        message: str = "Validation failed.",
        details: Any | None = None,
    ):

        super().__init__(
            message=message,
            status_code=400,
            details=details,
        )


class InvalidFileException(AuctionAIException):
    """
    Invalid upload file.
    """

    def __init__(
        self,
        message: str = "Invalid file uploaded.",
    ):

        super().__init__(
            message=message,
            status_code=400,
        )


class UnsupportedFileTypeException(AuctionAIException):
    """
    Unsupported upload format.
    """

    def __init__(
        self,
        message: str = "Unsupported file type.",
    ):

        super().__init__(
            message=message,
            status_code=415,
        )


# ==========================================================
# Upload Exceptions
# ==========================================================

class UploadException(AuctionAIException):
    """
    Upload failed.
    """

    def __init__(
        self,
        message: str = "File upload failed.",
    ):

        super().__init__(
            message=message,
            status_code=400,
        )


class FileStorageException(AuctionAIException):
    """
    Unable to store uploaded file.
    """

    def __init__(
        self,
        message: str = "Unable to store uploaded file.",
    ):

        super().__init__(
            message=message,
            status_code=500,
        )


# ==========================================================
# Image Processing
# ==========================================================

class ImageProcessingException(AuctionAIException):
    """
    Image preprocessing failed.
    """

    def __init__(
        self,
        message: str = "Image processing failed.",
    ):

        super().__init__(
            message=message,
            status_code=500,
        )


class LayoutDetectionException(AuctionAIException):
    """
    Layout detection failed.
    """

    def __init__(
        self,
        message: str = "Layout detection failed.",
    ):

        super().__init__(
            message=message,
            status_code=500,
        )


class AuctionSplitException(AuctionAIException):
    """
    Auction splitting failed.
    """

    def __init__(
        self,
        message: str = "Unable to split auction notices.",
    ):

        super().__init__(
            message=message,
            status_code=500,
        )


# ==========================================================
# OCR
# ==========================================================

class OCRException(AuctionAIException):
    """
    OCR failed.
    """

    def __init__(
        self,
        message: str = "OCR processing failed.",
    ):

        super().__init__(
            message=message,
            status_code=500,
        )


# ==========================================================
# Extraction
# ==========================================================

class RegexExtractionException(AuctionAIException):
    """
    Regex extraction failed.
    """

    def __init__(
        self,
        message: str = "Regex extraction failed.",
    ):

        super().__init__(
            message=message,
            status_code=500,
        )


class ParserException(AuctionAIException):
    """
    Parser failed.
    """

    def __init__(
        self,
        message: str = "Unable to parse OCR data.",
    ):

        super().__init__(
            message=message,
            status_code=500,
        )


class LLMException(AuctionAIException):
    """
    Gemini API failed.
    """

    def __init__(
        self,
        message: str = "LLM extraction failed.",
    ):

        super().__init__(
            message=message,
            status_code=502,
        )


class ConfidenceException(AuctionAIException):
    """
    Confidence score below threshold.
    """

    def __init__(
        self,
        message: str = "Low confidence extraction.",
    ):

        super().__init__(
            message=message,
            status_code=422,
        )


# ==========================================================
# Database
# ==========================================================

class DatabaseException(AuctionAIException):
    """
    Database operation failed.
    """

    def __init__(
        self,
        message: str = "Database operation failed.",
    ):

        super().__init__(
            message=message,
            status_code=500,
        )


class RecordNotFoundException(AuctionAIException):
    """
    Requested record not found.
    """

    def __init__(
        self,
        message: str = "Record not found.",
    ):

        super().__init__(
            message=message,
            status_code=404,
        )


class DuplicateRecordException(AuctionAIException):
    """
    Duplicate record.
    """

    def __init__(
        self,
        message: str = "Record already exists.",
    ):

        super().__init__(
            message=message,
            status_code=409,
        )


# ==========================================================
# Processing
# ==========================================================

class ProcessingException(AuctionAIException):
    """
    Pipeline processing failed.
    """

    def __init__(
        self,
        message: str = "Auction processing failed.",
    ):

        super().__init__(
            message=message,
            status_code=500,
        )


# ==========================================================
# Authentication
# ==========================================================

class AuthenticationException(AuctionAIException):
    """
    Authentication failed.
    """

    def __init__(
        self,
        message: str = "Authentication failed.",
    ):

        super().__init__(
            message=message,
            status_code=401,
        )


class AuthorizationException(AuctionAIException):
    """
    Authorization failed.
    """

    def __init__(
        self,
        message: str = "Access denied.",
    ):

        super().__init__(
            message=message,
            status_code=403,
        )