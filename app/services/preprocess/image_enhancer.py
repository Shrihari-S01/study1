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

    def enhance_crop_adaptive(
        self,
        crop_image_path: str,
    ) -> str:
        """
        Adaptive enhancement specifically for low-confidence / low-contrast notice crops:
        - CLAHE contrast enhancement
        - Unsharp mask / sharpening filter
        - Text deskew
        """
        try:
            image = cv2.imread(crop_image_path)
            if image is None:
                return crop_image_path

            # 1. Convert to Grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # 3. Sharpening Filter
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
            sharpened = cv2.filter2D(enhanced, -1, kernel)

            # 4. Deskew
            final_img = self.deskew(sharpened)

            enhanced_path = crop_image_path.replace(".jpg", "_enhanced.jpg").replace(".png", "_enhanced.png")
            cv2.imwrite(enhanced_path, final_img)
            logger.info("Saved adaptive enhanced crop: %s", enhanced_path)
            return enhanced_path
        except Exception as exc:
            logger.warning("Adaptive crop enhancement failed for %s: %s", crop_image_path, exc)
            return crop_image_path

    def expand_and_enhance_crop(
        self,
        full_image_path: str,
        bbox: dict,
        margin_percent: float = 0.15,
        output_crop_path: str = "",
    ) -> str:
        """
        Expands crop boundaries by margin_percent on all sides and applies adaptive contrast enhancement.
        Useful when OCR confidence is 0% or text is cut off at borders.
        """
        try:
            full_img = cv2.imread(full_image_path)
            if full_img is None:
                return output_crop_path or full_image_path

            h, w = full_img.shape[:2]
            x1 = float(bbox.get("x", 0))
            y1 = float(bbox.get("y", 0))
            bw = float(bbox.get("width", w))
            bh = float(bbox.get("height", h))
            x2 = x1 + bw
            y2 = y1 + bh

            # Expand boundaries by margin_percent
            pad_w = bw * margin_percent
            pad_h = bh * margin_percent

            new_x1 = max(0, int(x1 - pad_w))
            new_y1 = max(0, int(y1 - pad_h))
            new_x2 = min(w, int(x2 + pad_w))
            new_y2 = min(h, int(y2 + pad_h))

            expanded_crop = full_img[new_y1:new_y2, new_x1:new_x2]
            if expanded_crop.size == 0:
                return output_crop_path or full_image_path

            # Apply CLAHE and sharpening
            gray = cv2.cvtColor(expanded_crop, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
            sharpened = cv2.filter2D(enhanced, -1, kernel)

            save_path = output_crop_path or full_image_path.replace(".jpg", "_expanded_crop.jpg").replace(".png", "_expanded_crop.png")
            cv2.imwrite(save_path, sharpened)
            logger.info("Saved expanded crop (%dx%d padded to %dx%d): %s", int(bw), int(bh), new_x2 - new_x1, new_y2 - new_y1, save_path)
            return save_path
        except Exception as exc:
            logger.warning("Expanded crop creation failed: %s", exc)
            return output_crop_path or full_image_path

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

    def is_ready(
        self,
    ) -> bool:
        """
        Check service availability.
        """

        return True