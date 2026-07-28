"""
Image Enhancer.

Enhances newspaper images before OCR.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.core.logger import get_logger

logger = get_logger(__name__)


class ImageEnhancer:
    """
    Enhance newspaper image quality.
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Image Enhancer Initialized."
        )

    # ==========================================================
    # Enhance Image
    # ==========================================================

    def process(
        self,
        image_path: Path | str,
        output_path: Path | str | None = None,
    ) -> Path | str:
        """
        Enhance image for OCR.
        """
        if isinstance(image_path, str):
            return image_path
        return Path(image_path)

    # ==========================================================
    # Deskew Image
    # ==========================================================

    def deskew(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Detect text skew angle and rotate image to horizontal alignment.
        """
        try:
            # Create a binary thresholded version of the image to find text pixels
            binary = cv2.threshold(
                image,
                0,
                255,
                cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
            )[1]

            # Find coordinates of all foreground (text) pixels
            coords = np.column_stack(np.where(binary > 0))

            if len(coords) == 0:
                return image

            # Calculate minimum bounding rectangle for all text pixels
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]

            # Adjust OpenCV angle definition to standard rotation angle
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            # Ignore minor rotations or errors (above 20 degrees is likely not skew)
            if abs(angle) < 0.5 or abs(angle) > 20:
                return image

            # Perform affine rotation around the center
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                image,
                matrix,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )

            logger.info("Successfully deskewed image by %.2f degrees.", angle)
            return rotated

        except Exception as exc:
            logger.warning("Deskewing failed, returning original image: %s", exc)
            return image


    # ==========================================================
    # Contrast Enhancement
    # ==========================================================

    def enhance_contrast(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Improve local contrast using CLAHE.
        """

        clahe = cv2.createCLAHE(

            clipLimit=3.0,

            tileGridSize=(8, 8),

        )

        return clahe.apply(
            image,
        )

    # ==========================================================
    # Sharpen
    # ==========================================================

    def sharpen(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Sharpen text edges.
        """

        kernel = np.array(

            [

                [-1, -1, -1],

                [-1, 9, -1],

                [-1, -1, -1],

            ],

            dtype=np.float32,

        )

        return cv2.filter2D(

            image,

            -1,

            kernel,

        )

    # ==========================================================
    # Resize
    # ==========================================================

    def resize(
        self,
        image: np.ndarray,
        scale: float = 2.0,
    ) -> np.ndarray:
        """
        Enlarge image for OCR.
        """

        return cv2.resize(

            image,

            None,

            fx=scale,

            fy=scale,

            interpolation=cv2.INTER_CUBIC,

        )

    # ==========================================================
    # Gamma Correction
    # ==========================================================

    def gamma_correction(
        self,
        image: np.ndarray,
        gamma: float = 1.2,
    ) -> np.ndarray:
        """
        Adjust brightness.
        """

        inverse = 1.0 / gamma

        table = np.array(

            [

                ((i / 255.0) ** inverse) * 255

                for i in range(256)

            ],

            dtype="uint8",

        )

        return cv2.LUT(

            image,

            table,

        )

    # ==========================================================
    # Histogram Equalization
    # ==========================================================

    def equalize_histogram(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Improve global contrast.
        """

        return cv2.equalizeHist(
            image,
        )

    # ==========================================================
    # Morphological Enhancement
    # ==========================================================

    def morphology(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Enhance text regions.
        """

        kernel = np.ones(

            (2, 2),

            np.uint8,

        )

        return cv2.morphologyEx(

            image,

            cv2.MORPH_CLOSE,

            kernel,

        )

    # ==========================================================
    # Unsharp Mask
    # ==========================================================

    def unsharp_mask(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Increase text sharpness.
        """

        blurred = cv2.GaussianBlur(

            image,

            (0, 0),

            3,

        )

        return cv2.addWeighted(

            image,

            1.5,

            blurred,

            -0.5,

            0,

        )

    # ==========================================================
    # Health Check
    # ==========================================================

    def is_ready(
        self,
    ) -> bool:
        """
        Check service availability.
        """

        return True