"""
Image Utilities.

Common image helper functions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np

class ImageUtils:
    """
    Utility functions for image processing.
    """

    SUPPORTED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".bmp",
        ".tif",
        ".tiff",
        ".webp",
    }

    @staticmethod
    def exists(
        image_path: str,
    ) -> bool:
        """
        Check whether image exists.
        """

        return Path(image_path).is_file()

    @staticmethod
    def is_supported(
        image_path: str,
    ) -> bool:
        """
        Check supported image format.
        """

        extension = Path(image_path).suffix.lower()

        return extension in ImageUtils.SUPPORTED_EXTENSIONS

    @staticmethod
    def load(
        image_path: str,
    ) -> Optional[np.ndarray]:
        """
        Load image using OpenCV.
        """

        if not ImageUtils.exists(image_path):

            return None

        return cv2.imread(image_path)

    @staticmethod
    def save(
        image: np.ndarray,
        output_path: str,
    ) -> bool:
        """
        Save image.
        """

        return cv2.imwrite(
            output_path,
            image,
        )

    @staticmethod
    def dimensions(
        image: np.ndarray,
    ) -> tuple[int, int]:
        """
        Return image width and height.
        """

        height, width = image.shape[:2]

        return width, height

    @staticmethod
    def resize(
        image: np.ndarray,
        width: int,
        height: int,
    ) -> np.ndarray:
        """
        Resize image.
        """

        return cv2.resize(
            image,
            (width, height),
            interpolation=cv2.INTER_AREA,
        )

    @staticmethod
    def grayscale(
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert image to grayscale.
        """

        return cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

    @staticmethod
    def rgb(
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert BGR to RGB.
        """

        return cv2.cvtColor(
            image,
            cv2.COLOR_BGR2RGB,
        )

    @staticmethod
    def binary(
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert image to binary.
        """

        gray = ImageUtils.grayscale(
            image,
        )

        _, binary = cv2.threshold(

            gray,

            0,

            255,

            cv2.THRESH_BINARY + cv2.THRESH_OTSU,

        )

        return binary

    @staticmethod
    def rotate(
        image: np.ndarray,
        angle: float,
    ) -> np.ndarray:
        """
        Rotate image.
        """

        h, w = image.shape[:2]

        center = (w // 2, h // 2)

        matrix = cv2.getRotationMatrix2D(

            center,

            angle,

            1.0,

        )

        return cv2.warpAffine(

            image,

            matrix,

            (w, h),

        )

    @staticmethod
    def crop(
        image: np.ndarray,
        x: int,
        y: int,
        width: int,
        height: int,
    ) -> np.ndarray:
        """
        Crop image.
        """

        return image[
            y:y + height,
            x:x + width,
        ]

    @staticmethod
    def image_size(
        image_path: str,
    ) -> int:
        """
        Return image size in bytes.
        """

        return Path(image_path).stat().st_size

    @staticmethod
    def image_information(
        image_path: str,
    ) -> dict:
        """
        Return image metadata.
        """

        image = ImageUtils.load(
            image_path,
        )

        if image is None:

            return {}

        width, height = ImageUtils.dimensions(
            image,
        )

        return {

            "file_name": Path(image_path).name,

            "extension": Path(image_path).suffix,

            "width": width,

            "height": height,

            "channels": image.shape[2]
            if len(image.shape) == 3
            else 1,

            "size_bytes": ImageUtils.image_size(
                image_path,
            ),

        }

    @staticmethod
    def health_check() -> dict:
        """
        Utility health status.
        """

        return {

            "service": "Image Utils",

            "status": "Healthy",

            "opencv_available": True,

            "supported_formats": sorted(
                ImageUtils.SUPPORTED_EXTENSIONS,
            ),

        }