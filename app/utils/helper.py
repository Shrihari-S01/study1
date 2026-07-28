"""
Helper Utilities.

Common reusable helper functions.
"""

from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path
from typing import Any


class Helper:
    """
    Common helper methods.
    """

    @staticmethod
    def generate_uuid() -> str:
        """
        Generate UUID.
        """

        return str(uuid.uuid4())

    @staticmethod
    def file_name(file_path: str) -> str:
        """
        Return filename.
        """

        return Path(file_path).name

    @staticmethod
    def file_extension(file_path: str) -> str:
        """
        Return file extension.
        """

        return Path(file_path).suffix.lower()

    @staticmethod
    def file_stem(file_path: str) -> str:
        """
        Return filename without extension.
        """

        return Path(file_path).stem

    @staticmethod
    def create_directory(directory: str) -> None:
        """
        Create directory if not exists.
        """

        Path(directory).mkdir(

            parents=True,

            exist_ok=True,

        )

    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        Check file existence.
        """

        return Path(file_path).is_file()

    @staticmethod
    def directory_exists(directory: str) -> bool:
        """
        Check directory existence.
        """

        return Path(directory).is_dir()

    @staticmethod
    def file_size(file_path: str) -> int:
        """
        Return file size.
        """

        return os.path.getsize(
            file_path,
        )

    @staticmethod
    def md5(file_path: str) -> str:
        """
        Generate MD5 hash.
        """

        hash_md5 = hashlib.md5()

        with open(
            file_path,
            "rb",
        ) as file:

            for chunk in iter(

                lambda: file.read(4096),

                b"",

            ):

                hash_md5.update(
                    chunk,
                )

        return hash_md5.hexdigest()

    @staticmethod
    def remove_file(file_path: str) -> bool:
        """
        Delete file.
        """

        try:

            Path(file_path).unlink(

                missing_ok=True,

            )

            return True

        except Exception:

            return False

    @staticmethod
    def remove_directory(directory: str) -> bool:
        """
        Delete empty directory.
        """

        try:

            Path(directory).rmdir()

            return True

        except Exception:

            return False

    @staticmethod
    def safe_get(
        dictionary: dict,
        key: str,
        default: Any = "",
    ) -> Any:
        """
        Safe dictionary lookup.
        """

        return dictionary.get(
            key,
            default,
        )

    @staticmethod
    def clean_string(
        value: str,
    ) -> str:
        """
        Remove extra spaces.
        """

        if not value:

            return ""

        return " ".join(

            value.strip().split()

        )

    @staticmethod
    def is_empty(
        value: Any,
    ) -> bool:
        """
        Check empty value.
        """

        if value is None:

            return True

        if isinstance(
            value,
            str,
        ):

            return value.strip() == ""

        return False

    @staticmethod
    def remove_none(
        data: dict,
    ) -> dict:
        """
        Remove None values.
        """

        return {

            key: value

            for key, value in data.items()

            if value is not None

        }

    @staticmethod
    def health_check() -> dict:
        """
        Utility status.
        """

        return {

            "service": "Helper Utils",

            "status": "Healthy",

            "version": "1.0.0",

        }