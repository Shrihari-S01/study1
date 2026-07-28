"""
Auction Splitter.

Splits newspaper pages into individual auction notices.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from app.core.logger import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)

settings = get_settings()


class AuctionSplitter:
    """
    Detect and split auction notices.
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Auction Splitter Initialized."
        )

        self.minimum_width = 250

        self.minimum_height = 200

        self.minimum_area = 50000


    # ==========================================================
    # Load Image
    # ==========================================================

    def load_image(
        self,
        image_path: Path,
    ) -> np.ndarray:
        """
        Load newspaper image.
        """

        image = cv2.imread(
            str(image_path),
        )

        if image is None:

            raise ValueError(
                f"Unable to load image : {image_path}"
            )

        return image
    
    # ==========================================================
    # Convert to Gray
    # ==========================================================

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
    
    # ==========================================================
    # Threshold
    # ==========================================================

    def threshold(
        self,
        gray: np.ndarray,
    ) -> np.ndarray:
        """
        Convert to binary image.
        """

        return cv2.threshold(

            gray,

            0,

            255,

            cv2.THRESH_BINARY_INV
            |
            cv2.THRESH_OTSU,

        )[1]
    

    # ==========================================================
    # Connect Text Regions
    # ==========================================================

    def morphology(
        self,
        binary: np.ndarray,
    ) -> np.ndarray:
        """
        Connect nearby newspaper text.
        """

        kernel = cv2.getStructuringElement(

            cv2.MORPH_RECT,

            (35, 15),

        )

        return cv2.morphologyEx(

            binary,

            cv2.MORPH_CLOSE,

            kernel,

            iterations=2,

        )
    
    # ==========================================================
    # Find Contours
    # ==========================================================

    def find_contours(
        self,
        binary: np.ndarray,
    ):
        """
        Find auction contours.
        """

        contours, _ = cv2.findContours(

            binary,

            cv2.RETR_EXTERNAL,

            cv2.CHAIN_APPROX_SIMPLE,

        )

        return contours
    

    # ==========================================================
    # Split Newspaper
    # ==========================================================

    def split(
        self,
        image_path: Path | str,
    ) -> list[dict]:
        """
        Split newspaper into individual auction notices.

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
            "Splitting newspaper: %s",
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

        binary = self.morphology(
            binary,
        )

        contours = self.find_contours(
            binary,
        )

        notices = self.extract_regions(

            contours,

            image,

        )

        notices = self.filter_regions(
            notices,
        )

        notices = self.sort_regions(
            notices,
        )

        logger.info(

            "Detected %d auction notices.",

            len(notices),

        )

        return notices
    

    # ==========================================================
    # Extract Auction Regions
    # ==========================================================

    def extract_regions(
        self,
        contours,
        image: np.ndarray,
    ) -> list[dict]:
        """
        Extract auction regions.
        """

        notices = []

        image_height, image_width = image.shape[:2]

        for contour in contours:

            x, y, w, h = cv2.boundingRect(
                contour,
            )

            area = w * h

            if area < self.minimum_area:
                continue

            if w < self.minimum_width:
                continue

            if h < self.minimum_height:
                continue

            notices.append(

                {

                    "x": x,

                    "y": y,

                    "width": w,

                    "height": h,

                    "x2": x + w,

                    "y2": y + h,

                    "area": area,

                }

            )

        return notices
    

    # ==========================================================
    # Filter Auction Regions
    # ==========================================================

    def filter_regions(
        self,
        notices: list[dict],
    ) -> list[dict]:
        """
        Remove invalid auction regions.
        """

        filtered = []

        for notice in notices:

            if notice["area"] < self.minimum_area:

                continue

            filtered.append(
                notice,
            )

        logger.info(

            "Valid Auction Notices : %d",

            len(filtered),

        )

        return filtered
    

    # ==========================================================
    # Region Area
    # ==========================================================

    def area(
        self,
        notice: dict,
    ) -> int:
        """
        Calculate region area.
        """

        return (

            notice["width"]

            *

            notice["height"]

        )
    

    # ==========================================================
    # Sort Notices
    # ==========================================================

    def sort_regions(
        self,
        notices: list[dict],
    ) -> list[dict]:
        """
        Sort notices in newspaper reading order.
        """

        return sorted(

            notices,

            key=lambda n: (

                n["y"],

                n["x"],

            ),

        )
    

    # ==========================================================
    # Merge Regions
    # ==========================================================

    def merge_regions(
        self,
        notices: list[dict],
    ) -> list[dict]:
        """
        Merge nearby or overlapping auction regions.
        """

        if len(notices) <= 1:

            return notices

        merged = []

        notices = sorted(

            notices,

            key=lambda x: (

                x["y"],

                x["x"],

            ),

        )

        while notices:

            current = notices.pop(0)

            index = 0

            while index < len(notices):

                if self.should_merge(

                    current,

                    notices[index],

                ):

                    current = self.combine(

                        current,

                        notices.pop(index),

                    )

                else:

                    index += 1

            merged.append(current)

        logger.info(

            "Merged auction notices : %d",

            len(merged),

        )

        return merged
    

    # ==========================================================
    # Should Merge
    # ==========================================================

    def should_merge(
        self,
        region1: dict,
        region2: dict,
    ) -> bool:
        """
        Determine whether two auction regions
        belong to the same notice.
        """

        horizontal_gap = abs(

            region1["x2"]

            -

            region2["x"]

        )

        vertical_gap = abs(

            region1["y2"]

            -

            region2["y"]

        )

        overlap_x = min(

            region1["x2"],

            region2["x2"],

        ) - max(

            region1["x"],

            region2["x"],

        )

        overlap_y = min(

            region1["y2"],

            region2["y2"],

        ) - max(

            region1["y"],

            region2["y"],

        )

        if overlap_x > 40:

            return True

        if overlap_y > 40:

            return True

        if horizontal_gap < 30:

            return True

        if vertical_gap < 30:

            return True

        return False


    # ==========================================================
    # Combine Regions
    # ==========================================================

    def combine(
        self,
        region1: dict,
        region2: dict,
    ) -> dict:
        """
        Merge two auction regions.
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
    

    # ==========================================================
    # Remove Duplicate Regions
    # ==========================================================

    def remove_duplicates(
        self,
        notices: list[dict],
    ) -> list[dict]:
        """
        Remove duplicate auction detections.
        """

        unique = []

        for notice in notices:

            duplicate = False

            for saved in unique:

                if (

                    abs(notice["x"] - saved["x"]) < 10

                    and

                    abs(notice["y"] - saved["y"]) < 10

                    and

                    abs(notice["width"] - saved["width"]) < 10

                    and

                    abs(notice["height"] - saved["height"]) < 10

                ):

                    duplicate = True

                    break

            if not duplicate:

                unique.append(notice)

        logger.info(

            "Unique auction notices : %d",

            len(unique),

        )

        return unique
    

    # ==========================================================
    # Prepare Notices
    # ==========================================================

    def prepare(
        self,
        notices: list[dict],
    ) -> list[dict]:
        """
        Prepare final auction regions.
        """

        notices = self.merge_regions(

            notices,

        )

        notices = self.remove_duplicates(

            notices,

        )

        notices = self.sort_regions(

            notices,

        )

        return notices


    # ==========================================================
    # Save Auction Notices
    # ==========================================================

    def save_notices(
        self,
        image_path: Path | str,
        notices: list[dict],
        upload_number: str,
    ) -> list[dict]:
        """
        Crop and save individual auction notices.

        Parameters
        ----------
        image_path : Path | str

        notices : list[dict]

        upload_number : str

        Returns
        -------
        list[dict]
        """
        if isinstance(image_path, str):
            image_path = Path(image_path)

        image = self.load_image(
            image_path,
        )

        output_directory = (

            settings.split_dir

            /

            upload_number

        )

        output_directory.mkdir(

            parents=True,

            exist_ok=True,

        )

        saved_notices = []

        for index, notice in enumerate(

            notices,

            start=1,

        ):

            crop = image[

                notice["y"]:notice["y2"],

                notice["x"]:notice["x2"],

            ]

            filename = (

                f"auction_{index:03d}.png"

            )

            output_path = (

                output_directory

                /

                filename

            )

            cv2.imwrite(

                str(output_path),

                crop,

            )

            saved_notices.append(

                {

                    "auction_number": index,

                    "image_path": output_path,

                    "filename": filename,

                    "x": notice["x"],

                    "y": notice["y"],

                    "width": notice["width"],

                    "height": notice["height"],

                    "area": notice["area"],

                }

            )

        logger.info(

            "%d auction notices saved.",

            len(saved_notices),

        )

        return saved_notices



    # ==========================================================
    # Crop Auction
    # ==========================================================

    def crop_notice(
        self,
        image: np.ndarray,
        notice: dict,
    ) -> np.ndarray:
        """
        Crop a single auction notice.
        """

        return image[

            notice["y"]:notice["y2"],

            notice["x"]:notice["x2"],

        ]
    

    # ==========================================================
    # Create Split Folder
    # ==========================================================

    def create_output_directory(
        self,
        upload_number: str,
    ) -> Path:
        """
        Create folder for split auction notices.
        """

        directory = (

            settings.split_dir

            /

            upload_number

        )

        directory.mkdir(

            parents=True,

            exist_ok=True,

        )

        return directory
    

    # ==========================================================
    # Total Notices
    # ==========================================================

    def count(
        self,
        notices: list[dict],
    ) -> int:
        """
        Return total auction notices.
        """

        return len(
            notices,
        )
    

    # ==========================================================
    # Validate Notice
    # ==========================================================

    def validate_notice(
        self,
        notice: dict,
    ) -> bool:
        """
        Validate cropped notice.
        """

        if notice["width"] < self.minimum_width:

            return False

        if notice["height"] < self.minimum_height:

            return False

        if notice["area"] < self.minimum_area:

            return False

        return True
    

    # ==========================================================
    # Process Newspaper
    # ==========================================================

    def process(
        self,
        image_path: Path,
        upload_number: str,
    ) -> list[dict]:
        """
        Complete newspaper splitting pipeline.

        Parameters
        ----------
        image_path : Path

        upload_number : str

        Returns
        -------
        list[dict]
        """

        logger.info(
            "Starting auction splitting pipeline."
        )

        notices = self.split(
            image_path,
        )

        notices = self.prepare(
            notices,
        )

        saved = self.save_notices(

            image_path=image_path,

            notices=notices,

            upload_number=upload_number,

        )

        logger.info(
            "Auction splitting completed."
        )

        return saved
    

    # ==========================================================
    # Draw Auction Boxes
    # ==========================================================

    def draw_boxes(
        self,
        image_path: Path,
        notices: list[dict],
        output_path: Path,
    ) -> Path:
        """
        Draw detected auction boxes.
        """

        image = self.load_image(
            image_path,
        )

        for notice in notices:

            cv2.rectangle(

                image,

                (
                    notice["x"],
                    notice["y"],
                ),

                (
                    notice["x2"],
                    notice["y2"],
                ),

                (0, 255, 0),

                3,

            )

            cv2.putText(

                image,

                str(notice.get("auction_number", "")),

                (
                    notice["x"],
                    notice["y"] - 10,
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.7,

                (255, 0, 0),

                2,

            )

        cv2.imwrite(

            str(output_path),

            image,

        )

        logger.info(
            "Auction visualization saved."
        )

        return output_path
    
    # ==========================================================
    # Statistics
    # ==========================================================

    def statistics(
        self,
        notices: list[dict],
    ) -> dict:
        """
        Return splitter statistics.
        """

        if not notices:

            return {

                "total_notices": 0,

                "largest_notice": 0,

                "smallest_notice": 0,

                "average_area": 0,

            }

        areas = [

            notice["area"]

            for notice in notices

        ]

        return {

            "total_notices": len(notices),

            "largest_notice": max(areas),

            "smallest_notice": min(areas),

            "average_area": round(

                sum(areas) / len(areas),

                2,

            ),

        }

    # ==========================================================
    # Split Folder
    # ==========================================================

    def split_directory(
        self,
        upload_number: str,
    ) -> Path:
        """
        Return split directory.
        """

        return (

            settings.split_dir

            /

            upload_number

        )
    

    # ==========================================================
    # Health Check
    # ==========================================================

    def is_ready(
        self,
    ) -> bool:
        """
        Service health check.
        """

        try:

            settings.split_dir.mkdir(

                parents=True,

                exist_ok=True,

            )

            return True

        except Exception:

            logger.exception(
                "AuctionSplitter health check failed."
            )

            return False