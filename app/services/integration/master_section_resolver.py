"""
Master Section & Part ID Dynamic Resolver.

Resolves section_id and part_id dynamically from extracted asset_category and asset_type
or validates Angular master selections against the valid m_item_index_section table IDs.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)

# Master Table Definition: m_item_index_section
VALID_SECTION_IDS = {1, 2, 3, 12, 13, 14}

# Mapping: (asset_category, asset_type) -> (section_id, part_id)
MASTER_CATEGORY_MAPPING: Dict[Tuple[str, str], Tuple[int, int]] = {
    ("PROPERTY", "IMMOVABLE"): (12, 2),
    ("PROPERTY", "MOVABLE"): (12, 1),
    ("REAL ESTATE", "IMMOVABLE"): (12, 2),
    ("LAND", "IMMOVABLE"): (12, 2),
    ("BUILDING", "IMMOVABLE"): (12, 2),
    ("HOUSE", "IMMOVABLE"): (12, 2),
    ("PLOT", "IMMOVABLE"): (12, 2),

    ("VEHICLE", "MOVABLE"): (3, 1),
    ("CAR", "MOVABLE"): (3, 1),
    ("AUTOMOBILE", "MOVABLE"): (3, 1),

    ("GOLD", "MOVABLE"): (2, 1),
    ("JEWELRY", "MOVABLE"): (2, 1),

    ("SCRAP", "MOVABLE"): (1, 1),

    ("PEARL", "MOVABLE"): (13, 1),
}

class MasterSectionResolver:
    """
    Dynamic resolver for section_id and part_id driven by master metadata.
    """

    @classmethod
    def resolve_section_and_part(
        cls,
        payload: Dict[str, Any],
        processing_id: str = "N/A",
    ) -> Tuple[Optional[int], Optional[int], bool, str]:
        """
        Dynamically resolve section_id and part_id from extracted asset_category and asset_type.

        Returns:
            Tuple[section_id: Optional[int], part_id: Optional[int], is_valid: bool, status_message: str]
        """
        # 1. Check if payload already contains explicit section_id
        raw_sec = payload.get("section_id")
        raw_part = payload.get("part_id")

        if raw_sec is not None and str(raw_sec).strip().isdigit():
            sec_int = int(str(raw_sec).strip())
            part_int = int(str(raw_part).strip()) if raw_part is not None and str(raw_part).strip().isdigit() else 1

            if sec_int in VALID_SECTION_IDS:
                logger.info(
                    "\n==================================================\n"
                    "[MASTER SECTION RESOLUTION]\n"
                    "Explicit section_id provided: %d (Valid Master ID)\n"
                    "Status: PASS\n"
                    "==================================================",
                    sec_int,
                )
                return sec_int, part_int, True, "PASS"
            else:
                err_msg = f"INVALID_SECTION_ID: Provided section_id {sec_int} does not exist in master table m_item_index_section {sorted(list(VALID_SECTION_IDS))}."
                logger.error("[%s] %s", processing_id, err_msg)
                return None, None, False, err_msg

        # 2. Extract asset_category and asset_type
        raw_category = str(payload.get("asset_category") or payload.get("category") or payload.get("property_type") or "PROPERTY").strip().upper()
        raw_type = str(payload.get("asset_type") or payload.get("property_subtype") or "IMMOVABLE").strip().upper()

        # Clean category token (e.g. "RESIDENTIAL PROPERTY" -> "PROPERTY")
        clean_cat = "PROPERTY" if any(w in raw_category for w in ["PROPERTY", "HOUSE", "PLOT", "LAND", "FLAT", "SHOP"]) else raw_category
        clean_cat = "VEHICLE" if any(w in raw_category for w in ["VEHICLE", "CAR", "AUTO", "TRUCK"]) else clean_cat
        clean_cat = "GOLD" if any(w in raw_category for w in ["GOLD", "JEWEL"]) else clean_cat

        clean_type = "MOVABLE" if "MOVABLE" in raw_type and "IMMOVABLE" not in raw_type else "IMMOVABLE"

        matched = MASTER_CATEGORY_MAPPING.get((clean_cat, clean_type))

        if not matched:
            # Fallback check by category only
            for (cat, typ), sec_tuple in MASTER_CATEGORY_MAPPING.items():
                if cat in clean_cat:
                    matched = sec_tuple
                    break

        if matched:
            sec_id, part_id = matched
            logger.info(
                "\n==================================================\n"
                "[MASTER SECTION RESOLUTION]\n"
                "Extracted:\n"
                "  Category = %s\n"
                "  Type     = %s\n\n"
                "Matched Master:\n"
                "  section_id = %d\n"
                "  part_id    = %d\n\n"
                "Status:\n"
                "  PASS\n"
                "==================================================",
                raw_category,
                raw_type,
                sec_id,
                part_id,
            )
            return sec_id, part_id, True, "PASS"

        err_msg = f"NO_MASTER_MAPPING_FOUND: No matching m_item_index_section master mapping found for Category='{raw_category}', Type='{raw_type}'."
        logger.error("[%s] %s", processing_id, err_msg)
        return None, None, False, err_msg
