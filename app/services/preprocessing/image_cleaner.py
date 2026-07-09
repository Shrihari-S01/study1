"""Image cleaning operations."""

from pathlib import Path

import cv2
import numpy as np


class ImageCleaner:
    """Remove basic noise and improve text contrast."""

    def clean(self, input_path: Path, output_path: Path) -> Path:
        """Clean an image and write it to output_path."""
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError(f"Could not read image: {input_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=20)
        threshold = cv2.adaptiveThreshold(
            denoised,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(threshold, cv2.MORPH_CLOSE, kernel)
        cv2.imwrite(str(output_path), cleaned)
        return output_path 

