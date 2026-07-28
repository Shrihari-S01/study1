"""
Image Cleaner.

Removes noise and improves image quality before OCR.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.core.logger import get_logger

logger = get_logger(__name__)


class ImageCleaner:
    """
    Clean newspaper images before OCR.
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Image Cleaner Initialized."
        )

    # ==========================================================
    # Clean Image
    # ==========================================================

    def process(
        self,
        image_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Clean newspaper image.

        Parameters
        ----------
        image_path : Path

        output_path : Path

        Returns
        -------
        Path
        """

        logger.info(
            "Cleaning image: %s",
            image_path.name,
        )

        image = cv2.imread(
            str(image_path),
        )

        if image is None:

            raise ValueError(
                f"Unable to read image: {image_path}"
            )

        image = self.to_gray(
            image,
        )

        image = self.remove_noise(
            image,
        )

        image = self.adaptive_threshold(
            image,
        )

        image = self.remove_small_noise(
            image,
        )

        cv2.imwrite(
            str(output_path),
            image,
        )

        logger.info(
            "Image cleaning completed."
        )

        return output_path

    # ==========================================================
    # Convert to Gray
    # ==========================================================

    def to_gray(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert image to grayscale.
        """

        if len(image.shape) == 3:

            return cv2.cvtColor(

                image,

                cv2.COLOR_BGR2GRAY,

            )

        return image

    # ==========================================================
    # Remove Noise
    # ==========================================================

    def remove_noise(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Remove salt-and-pepper noise.
        """

        return cv2.fastNlMeansDenoising(

            image,

            None,

            10,

            7,

            21,

        )

    # ==========================================================
    # Adaptive Threshold
    # ==========================================================

    def adaptive_threshold(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert image into black & white.
        """

        return cv2.adaptiveThreshold(

            image,

            255,

            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,

            cv2.THRESH_BINARY,

            31,

            15,

        )

    # ==========================================================
    # Remove Small Dots
    # ==========================================================

    def remove_small_noise(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Remove tiny dots.
        """

        kernel = np.ones(

            (2, 2),

            np.uint8,

        )

        image = cv2.morphologyEx(

            image,

            cv2.MORPH_OPEN,

            kernel,

        )

        image = cv2.morphologyEx(

            image,

            cv2.MORPH_CLOSE,

            kernel,

        )

        return image

    # ==========================================================
    # Median Blur
    # ==========================================================

    def median_blur(
        self,
        image: np.ndarray,
        kernel_size: int = 3,
    ) -> np.ndarray:
        """
        Reduce impulse noise.
        """

        return cv2.medianBlur(

            image,

            kernel_size,

        )

    # ==========================================================
    # Gaussian Blur
    # ==========================================================

    def gaussian_blur(
        self,
        image: np.ndarray,
        kernel_size: int = 3,
    ) -> np.ndarray:
        """
        Smooth image.
        """

        return cv2.GaussianBlur(

            image,

            (kernel_size, kernel_size),

            0,

        )

    # ==========================================================
    # Sharpen Image
    # ==========================================================

    def sharpen(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Sharpen text.
        """

        kernel = np.array(

            [

                [0, -1, 0],

                [-1, 5, -1],

                [0, -1, 0],

            ]

        )

        return cv2.filter2D(

            image,

            -1,

            kernel,

        )

    # ==========================================================
    # Invert Image
    # ==========================================================

    def invert(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Invert colors.
        """

        return cv2.bitwise_not(

            image,

        )

    # ==========================================================
    # Resize Image
    # ==========================================================

    def resize(
        self,
        image: np.ndarray,
        scale: float = 2.0,
    ) -> np.ndarray:
        """
        Resize image.

        Enlarging small newspaper text
        improves OCR accuracy.
        """

        return cv2.resize(

            image,

            None,

            fx=scale,

            fy=scale,

            interpolation=cv2.INTER_CUBIC,

        )

    # ==========================================================
    # CLAHE Contrast
    # ==========================================================

    def enhance_contrast(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Improve local contrast.
        """

        clahe = cv2.createCLAHE(

            clipLimit=2.0,

            tileGridSize=(8, 8),

        )

        return clahe.apply(

            image,

        )

    # ==========================================================
    # Health Check
    # ==========================================================

    def is_ready(
        self,
    ) -> bool:
        """
        Service readiness.
        """

        return True