"""
Asset & Category Parser for PDF Auction Processing Pipeline.
Maps specific asset categories (Battery, Iron & Steel, Plastic, Rubber, Property) and asset types.
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)


class CategoryParser:
    """
    Parses asset category, product type, and asset_type (Movable / Immovable).
    """

    def parse_category(self, text: str, description: str = "") -> dict:
        """
        Determine asset category and asset type.
        """
        combined = (text or "") + " " + (description or "")
        t_upper = combined.upper()

        category_data = {
            "asset_category": "Miscellaneous Items",
            "property_type": None,
            "product_type": None,
            "asset_type": "Movable"
        }

        # 1. Clean explicit Category header from current lot text if present
        cat_hdr = re.search(r'(?i)(?:Category\s*[-:]?)\s*([^\n]+)', text)
        if cat_hdr:
            raw_c = cat_hdr.group(1).strip()
            # Clean trailing numbers, hyphens, parentheses, or dots (e.g. "Battery - 0.0" -> "Battery")
            clean_c = re.sub(r'[\)\-0-9.:\s]+$', '', raw_c).strip()
            clean_c = re.sub(r'^[\)\-0-9.:\s]+', '', clean_c).strip(' -,\t\r\n')
            if clean_c and len(clean_c) > 1 and clean_c.lower() not in (")", "-", "0.0", "pcb group", "("):
                category_data["asset_category"] = clean_c

        # 2. Specific Category Mapping Override
        if "BATTERY" in t_upper or "LEAD ACID" in t_upper:
            category_data["asset_category"] = "Battery"
            category_data["asset_type"] = "Movable"
        elif "IRON" in t_upper or "STEEL" in t_upper or "FERROUS" in t_upper:
            category_data["asset_category"] = "Iron & Steel"
            category_data["asset_type"] = "Movable"
        elif "PLASTIC" in t_upper or "PVC" in t_upper:
            category_data["asset_category"] = "Plastic"
            category_data["asset_type"] = "Movable"
        elif "RUBBER" in t_upper or "TYRE" in t_upper:
            category_data["asset_category"] = "Rubber"
            category_data["asset_type"] = "Movable"
        elif "FLAT" in t_upper or "LAND" in t_upper or "PLOT" in t_upper or "BUILDING" in t_upper or "REAL ESTATE" in t_upper or "PROPERTY" in t_upper:
            category_data["asset_category"] = "property"
            category_data["asset_type"] = "Immovable"

        return category_data
