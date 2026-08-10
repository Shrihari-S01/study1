"""
Lot Parser for PDF Auction Processing Pipeline.
Dynamically segments lot blocks and parses lot numbers, descriptions, locations, quantities, and units.
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)

class LotParser:
    """
    Dynamically segments lot blocks across any number of lots (1 to 250+) and extracts lot fields.
    """

    def segment_lots(self, lot_section_text: str) -> list[dict]:
        """
        Dynamically split lot_section_text into lot block dicts.
        Supported markers: Lot No, Lot Number, Lot #, Item No, LOT ID.
        """
        if not lot_section_text:
            return []

        # Structural marker regex for starting a lot
        marker_pattern = r'(?i)(?:^|\n)\s*(Lot\s+No\s*[-:#]?|Lot\s+Number\s*[-:#]?|Lot\s*#|Item\s+No\s*[-:#]?|LOT\s+ID\s*[-:#]?)\s*(\d+(?:\.\d+)?[a-zA-Z]?)'
        matches = list(re.finditer(marker_pattern, lot_section_text))

        if not matches:
            # Fallback for plain "Lot No - 1.0" or "Lot 1"
            marker_pattern = r'(?i)\b(Lot\s+No|Lot|Item)\s*[-:#]?\s*(\d+(?:\.\d+)?)'
            matches = list(re.finditer(marker_pattern, lot_section_text))

        if not matches:
            return []

        # Deduplicate matches by lot number
        seen_lots = set()
        unique_matches = []
        for m in matches:
            lot_id = m.group(2).strip()
            if lot_id not in seen_lots:
                seen_lots.add(lot_id)
                unique_matches.append(m)

        lot_blocks = []
        for i in range(len(unique_matches)):
            start_idx = unique_matches[i].start()
            end_idx = unique_matches[i + 1].start() if i + 1 < len(unique_matches) else len(lot_section_text)
            raw_text = lot_section_text[start_idx:end_idx].strip()

            lot_no_val = unique_matches[i].group(2).strip()
            # Normalize lot_no (e.g. 1.0 -> 1)
            if lot_no_val.endswith(".0"):
                clean_lot_no = lot_no_val[:-2]
            else:
                clean_lot_no = lot_no_val

            lot_blocks.append({
                "lot_no": clean_lot_no,
                "raw_lot_no": lot_no_val,
                "raw_text": raw_text
            })

        logger.info("Dynamic Lot Segmentation Completed: Detected %d Lot Blocks.", len(lot_blocks))
        return lot_blocks

    def parse_lot_block(self, lot_blk: dict) -> dict:
        """
        Extract lot-level fields from raw_text.
        """
        text = lot_blk.get("raw_text", "")
        lot_data = {
            "lot_no": lot_blk.get("lot_no"),
            "auction_description": None,
            "quantity": None,
            "units": None,
            "assets_location": None,
            "state": None,
            "raw_text": text
        }

        if not text:
            return lot_data

        # 1. Multi-Line Lot Name & Full Material Description Parsing (Requirement 4)
        lot_name_str = ""
        lot_desc_str = ""

        # Extract Lot Name (e.g. BRASS SCRAP & MISCELLANEOUS)
        name_m = re.search(r'(?i)Lot\s+Name\s*[-:]?\s*([\s\S]*?)(?=Product\s+Type|Category|1\)\s*EMD|Quantity|Start\s+Price|$)', text)
        if name_m:
            raw_n = name_m.group(1).strip()
            clean_n = " ".join([ln.strip() for ln in raw_n.splitlines() if ln.strip()])
            clean_n = re.sub(r'[\s,\-]+$', '', clean_n).strip()
            if clean_n:
                lot_name_str = clean_n

        # Extract Full Material Description Column (e.g. BRASS SCRAP - 2951.83 KG...)
        desc_blk = re.search(r'(?i)(?:Lot\s+Description[\s\n\r]+)?([A-Za-z0-9\s,\(\)\-:\./]+?)(?=QUANTITY\s+MENTIONED|1\)\s*EMD|Quantity|Start\s+Price|Post\s+Bid|$)', text)
        if desc_blk:
            raw_d = desc_blk.group(1).strip()
            clean_d = " ".join([ln.strip() for ln in raw_d.splitlines() if ln.strip()])
            clean_d = re.sub(r'[\s,\-]+$', '', clean_d).strip()
            if clean_d:
                lot_desc_str = clean_d

        # Combine Lot Name + Material Description without truncation
        if lot_name_str and lot_desc_str and lot_name_str.upper() not in lot_desc_str.upper():
            combined_desc = f"{lot_name_str} - {lot_desc_str}"
        else:
            combined_desc = lot_name_str or lot_desc_str

        if combined_desc:
            lot_data["auction_description"] = combined_desc

        # 2. Quantity & Units (e.g. Quantity - 20.0 MT or Quantity - 1.0 LOT)
        qty_m = re.search(r'(?i)(?:Quantity|Qty)\s*[-:]?\s*(\d+(?:\.\d+)?)\s*([A-Za-z]+)?', text)
        if qty_m:
            try:
                lot_data["quantity"] = float(qty_m.group(1))
            except Exception:
                pass
            if qty_m.group(2) and qty_m.group(2).upper() not in ("MENTIONED", "IS", "INDICATIVE", "ILLUSTRATIVE"):
                lot_data["units"] = qty_m.group(2).strip()

        # 3. Multi-Line Lot Location & State
        loc_m = re.search(r'(?i)(?:Lot\s+Location|Location|Address)\s*[-:]?\s*([\s\S]*?)(?=Lot\s+State|Bid\s+Valid|State|Pre-Bid|No\s+document|$)', text)
        if loc_m:
            raw_loc = loc_m.group(1).strip()
            clean_loc = ", ".join([ln.strip() for ln in raw_loc.splitlines() if ln.strip()])
            clean_loc = re.sub(r'(\s*,\s*)+', ', ', clean_loc).strip(' ,-')
            if clean_loc:
                lot_data["assets_location"] = clean_loc

        state_m = re.search(r'(?i)(?:Lot\s+State|State)\s*[-:]?\s*([A-Za-z\s]+)', text)
        if state_m:
            lot_data["state"] = state_m.group(1).strip()

        return lot_data
