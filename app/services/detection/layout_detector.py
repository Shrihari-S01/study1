"""
Layout Detector.

Detects newspaper layout regions before auction splitting.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.core.logger import get_logger

logger = get_logger(__name__)

class LayoutDetector:
    """
    Detect newspaper layout blocks.
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Layout Detector Initialized."
        )

        self.minimum_width = 150

        self.minimum_height = 80

        self.minimum_area = 12000

    def load_image(
        self,
        image_path: Path,
    ) -> np.ndarray:
        """
        Load image.
        """

        image = cv2.imread(
            str(image_path),
        )

        if image is None:

            raise ValueError(
                f"Unable to read image: {image_path}"
            )

        return image

    def gray(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert image to grayscale.
        """

        return cv2.cvtColor(

            image,

            cv2.COLOR_BGR2GRAY,

        )

    def threshold(
        self,
        gray: np.ndarray,
    ) -> np.ndarray:
        """
        Create binary image.
        """

        return cv2.threshold(

            gray,

            0,

            255,

            cv2.THRESH_BINARY_INV
            |
            cv2.THRESH_OTSU,

        )[1]
    

    def detect(
        self,
        image_path: Path | str,
    ) -> list[dict]:
        """
        Alias for detect_layout used by Pipeline.
        """
        if isinstance(image_path, str):
            image_path = Path(image_path)
        return self.detect_layout(image_path)

    def detect_layout(
        self,
        image_path: Path | str,
    ) -> list[dict]:
        """
        Detect newspaper layout regions.

        Parameters
        ----------
        image_path : Path | str

        Returns
        -------
        list[dict]
        """
        if isinstance(image_path, str):
            image_path = Path(image_path)

        logger.info(
            "Detecting layout: %s",
            image_path.name,
        )

        image = self.load_image(
            image_path,
        )

        gray = self.gray(
            image,
        )

        binary = self.threshold(
            gray,
        )

        binary = self.close_regions(
            binary,
        )

        contours = self.find_contours(
            binary,
        )

        regions = self.extract_regions(

            contours,

            image,

        )

        regions = self.sort_regions(
            regions,
        )

        logger.info(

            "Detected %d layout regions.",

            len(regions),

        )

        return regions
    

    def close_regions(
        self,
        binary: np.ndarray,
    ) -> np.ndarray:
        """
        Merge nearby text blocks.
        """

        kernel = cv2.getStructuringElement(

            cv2.MORPH_RECT,

            (25, 15),

        )

        return cv2.morphologyEx(

            binary,

            cv2.MORPH_CLOSE,

            kernel,

            iterations=2,

        )
    

    def find_contours(
        self,
        binary: np.ndarray,
    ):
        """
        Find newspaper contours.
        """

        contours, _ = cv2.findContours(

            binary,

            cv2.RETR_EXTERNAL,

            cv2.CHAIN_APPROX_SIMPLE,

        )

        return contours
    

    def extract_regions(
        self,
        contours,
        image: np.ndarray,
    ) -> list[dict]:
        """
        Extract valid newspaper regions.
        """

        regions = []

        image_height, image_width = image.shape[:2]

        for contour in contours:

            x, y, w, h = cv2.boundingRect(
                contour,
            )

            area = w * h

            # Ignore tiny regions
            if area < self.minimum_area:
                continue

            if w < self.minimum_width:
                continue

            if h < self.minimum_height:
                continue

            # Ignore extremely narrow regions
            if w > image_width * 0.98 and h < 60:
                continue

            region = {

                "x": x,

                "y": y,

                "width": w,

                "height": h,

                "area": area,

                "x2": x + w,

                "y2": y + h,

            }

            regions.append(region)

        logger.info(

            "Valid regions detected: %d",

            len(regions),

        )

        return regions
    

    def area(
        self,
        region: dict,
    ) -> int:
        """
        Calculate region area.
        """

        return (

            region["width"]

            *

            region["height"]

        )

    def filter_regions(
        self,
        regions: list[dict],
    ) -> list[dict]:
        """
        Remove invalid regions.
        """

        filtered = []

        for region in regions:

            if self.area(region) < self.minimum_area:

                continue

            filtered.append(
                region,
            )

        logger.info(

            "Remaining Regions: %d",

            len(filtered),

        )

        return filtered
    

    def center(
        self,
        region: dict,
    ) -> tuple[int, int]:
        """
        Return center point.
        """

        return (

            region["x"] + region["width"] // 2,

            region["y"] + region["height"] // 2,

        )

    def merge_regions(
        self,
        regions: list[dict],
        overlap_threshold: float = 0.30,
    ) -> list[dict]:
        """
        Merge overlapping layout regions.
        """

        if not regions:

            return []

        merged = []

        regions = sorted(

            regions,

            key=lambda r: (

                r["y"],

                r["x"],

            ),

        )

        while regions:

            current = regions.pop(0)

            merged_region = current.copy()

            remaining = []

            for region in regions:

                if self.is_overlapping(

                    merged_region,

                    region,

                    overlap_threshold,

                ):

                    merged_region = self.combine_regions(

                        merged_region,

                        region,

                    )

                else:

                    remaining.append(

                        region,

                    )

            merged.append(

                merged_region,

            )

            regions = remaining

        logger.info(

            "Merged Regions : %d",

            len(merged),

        )

        return merged
    

    def is_overlapping(
        self,
        box1: dict,
        box2: dict,
        threshold: float = 0.30,
    ) -> bool:
        """
        Check whether two regions overlap.
        """

        x_left = max(

            box1["x"],

            box2["x"],

        )

        y_top = max(

            box1["y"],

            box2["y"],

        )

        x_right = min(

            box1["x2"],

            box2["x2"],

        )

        y_bottom = min(

            box1["y2"],

            box2["y2"],

        )

        if x_right <= x_left:

            return False

        if y_bottom <= y_top:

            return False

        intersection = (

            x_right - x_left

        ) * (

            y_bottom - y_top

        )

        area1 = box1["area"]

        area2 = box2["area"]

        smaller = min(

            area1,

            area2,

        )

        ratio = intersection / smaller

        return ratio >= threshold

    def combine_regions(
        self,
        region1: dict,
        region2: dict,
    ) -> dict:
        """
        Combine two layout regions.
        """

        x = min(

            region1["x"],

            region2["x"],

        )

        y = min(

            region1["y"],

            region2["y"],

        )

        x2 = max(

            region1["x2"],

            region2["x2"],

        )

        y2 = max(

            region1["y2"],

            region2["y2"],

        )

        width = x2 - x

        height = y2 - y

        return {

            "x": x,

            "y": y,

            "width": width,

            "height": height,

            "x2": x2,

            "y2": y2,

            "area": width * height,

        }

    def sort_regions(
        self,
        regions: list[dict],
    ) -> list[dict]:
        """
        Sort regions in newspaper reading order.
        """

        return sorted(

            regions,

            key=lambda r: (

                r["y"],

                r["x"],

            ),

        )
    

    def save_regions(
        self,
        image_path: Path,
        regions: list[dict],
        output_directory: Path,
    ) -> list[Path]:
        """
        Crop and save detected layout regions.

        Returns
        -------
        list[Path]
        """

        image = self.load_image(
            image_path,
        )

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        saved_files = []

        for index, region in enumerate(regions, start=1):

            crop = image[
                region["y"]:region["y2"],
                region["x"]:region["x2"],
            ]

            file_path = (
                output_directory
                /
                f"region_{index:03d}.png"
            )

            cv2.imwrite(
                str(file_path),
                crop,
            )

            saved_files.append(
                file_path,
            )

        logger.info(
            "Saved %d layout regions.",
            len(saved_files),
        )

        return saved_files
    

    def draw_regions(
        self,
        image_path: Path,
        regions: list[dict],
        output_path: Path,
    ) -> Path:
        """
        Draw detected layout regions.
        """

        image = self.load_image(
            image_path,
        )

        for region in regions:

            cv2.rectangle(

                image,

                (region["x"], region["y"]),

                (region["x2"], region["y2"]),

                (0, 255, 0),

                3,

            )

        cv2.imwrite(
            str(output_path),
            image,
        )

        logger.info(
            "Layout visualization saved."
        )

        return output_path
    

    def statistics(
        self,
        regions: list[dict],
    ) -> dict:
        """
        Layout statistics.
        """

        if not regions:

            return {

                "total_regions": 0,

                "largest_area": 0,

                "smallest_area": 0,

                "average_area": 0,

            }

        areas = [

            region["area"]

            for region in regions

        ]

        return {

            "total_regions": len(regions),

            "largest_area": max(areas),

            "smallest_area": min(areas),

            "average_area": round(

                sum(areas) / len(areas),

                2,

            ),

        }
    

    def is_ready(
        self,
    ) -> bool:
        """
        Service health.
        """

        return True