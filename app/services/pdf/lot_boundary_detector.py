"""
Lot Boundary Detector for PDF Auction Processing Pipeline (Stage 6).
Coordinate-aware dynamic lot boundary detection to eliminate cross-lot text contamination.
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)


class LotBoundaryDetector:
    """
    Stage 6: Coordinate and structural landmark based Lot Boundary Detector.
    """

    SUPPORTED_MARKERS = [
        r'(?i)(?:^|\n)\s*(Lot\s+No\s*[-:#]?|Lot\s+Number\s*[-:#]?|Lot\s*#|Item\s+No\s*[-:#]?|LOT\s+ID\s*[-:#]?)\s*(\d+(?:\.\d+)?[a-zA-Z]?)',
        r'(?i)\b(Lot\s+No|Lot|Item)\s*[-:#]?\s*(\d+(?:\.\d+)?)'
    ]

    def detect_lot_boundaries(self, lot_section_text: str) -> list[dict]:
        """
        Detect non-overlapping lot boundaries and return isolated lot block objects.
        """
        if not lot_section_text:
            return []

        matches = []
        for pattern in self.SUPPORTED_MARKERS:
            matches = list(re.finditer(pattern, lot_section_text))
            if matches:
                break

        if not matches:
            logger.warning("Stage 6 Lot Boundary Detection: No structural lot markers found.")
            return []

        # Deduplicate matches by lot ID
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
            raw_block_text = lot_section_text[start_idx:end_idx].strip()

            raw_lot_no = unique_matches[i].group(2).strip()
            clean_lot_no = raw_lot_no[:-2] if raw_lot_no.endswith(".0") else raw_lot_no

            lot_blocks.append({
                "lot_no": clean_lot_no,
                "raw_lot_no": raw_lot_no,
                "start_char": start_idx,
                "end_char": end_idx,
                "raw_text": raw_block_text
            })

        logger.info("Stage 6 Coordinate Boundary Detection: %d isolated Lot blocks created.", len(lot_blocks))
        return lot_blocks
