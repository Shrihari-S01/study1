"""
Deskew Service.

Corrects the skew angle of newspaper images.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.core.logger import get_logger

logger = get_logger(__name__)


class DeskewService:
    """
    Correct image skew.
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Deskew Service Initialized."
        )

    # ==========================================================
    # Deskew Image
    # ==========================================================

    def process(
        self,
        image_path: Path,
        output_path: Path,
    ) -> Path:
        """
        Correct image skew.

        Parameters
        ----------
        image_path : Path

        output_path : Path

        Returns
        -------
        Path
        """

        logger.info(
            "Deskewing image: %s",
            image_path.name,
        )

        image = cv2.imread(
            str(image_path),
        )

        if image is None:

            raise ValueError(
                f"Unable to read image: {image_path}"
            )

        angle = self.detect_angle(
            image,
        )

        corrected = self.rotate(
            image,
            angle,
        )

        cv2.imwrite(
            str(output_path),
            corrected,
        )

        logger.info(
            "Deskew completed."
        )

        return output_path

    # ==========================================================
    # Detect Skew Angle
    # ==========================================================

    def detect_angle(
        self,
        image: np.ndarray,
    ) -> float:
        """
        Detect skew angle.
        """

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        gray = cv2.bitwise_not(
            gray,
        )

        threshold = cv2.threshold(

            gray,

            0,

            255,

            cv2.THRESH_BINARY | cv2.THRESH_OTSU,

        )[1]

        coordinates = np.column_stack(

            np.where(
                threshold > 0,
            )

        )

        if len(coordinates) == 0:

            return 0.0

        angle = cv2.minAreaRect(
            coordinates,
        )[-1]

        if angle < -45:

            angle = 90 + angle

        else:

            angle = -angle

        logger.info(
            "Detected skew angle: %.2f",
            angle,
        )

        return angle

    # ==========================================================
    # Rotate Image
    # ==========================================================

    def rotate(
        self,
        image: np.ndarray,
        angle: float,
    ) -> np.ndarray:
        """
        Rotate image.
        """

        (height, width) = image.shape[:2]

        center = (
            width // 2,
            height // 2,
        )

        matrix = cv2.getRotationMatrix2D(

            center,

            angle,

            1.0,

        )

        rotated = cv2.warpAffine(

            image,

            matrix,

            (width, height),

            flags=cv2.INTER_CUBIC,

            borderMode=cv2.BORDER_REPLICATE,

        )

        return rotated

    # ==========================================================
    # Is Skewed
    # ==========================================================

    def is_skewed(
        self,
        image_path: Path,
        threshold: float = 1.0,
    ) -> bool:
        """
        Check if image is skewed.
        """

        image = cv2.imread(
            str(image_path),
        )

        if image is None:

            return False

        angle = self.detect_angle(
            image,
        )

        return abs(angle) > threshold

    # ==========================================================
    # Get Skew Angle
    # ==========================================================

    def get_angle(
        self,
        image_path: Path,
    ) -> float:
        """
        Return skew angle.
        """

        image = cv2.imread(
            str(image_path),
        )

        if image is None:

            return 0.0

        return self.detect_angle(
            image,
        )