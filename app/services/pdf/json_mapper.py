"""
JSON Mapper for PDF Auction Processing Pipeline (Stage 15).
Serializes validated, normalized records into the final API schema without performing extraction or guessing.
"""

from app.core.logger import get_logger

logger = get_logger(__name__)

class JSONMapper:
    """
    Stage 15: JSON Mapper for final API schema serialization.
    """

    def serialize_records(self, validated_records: list[dict]) -> list[dict]:
        """
        Serialize validated lot records into clean JSON API records.
        """
        json_records = []
        for rec in validated_records:
            clean_rec = rec.copy()
            # Remove internal extraction metadata keys before JSON response
            clean_rec.pop("sources", None)
            clean_rec.pop("raw_text", None)
            clean_rec.pop("raw_lot_no", None)
            json_records.append(clean_rec)

        logger.info("Stage 15 JSON Mapper: Serialized %d clean records.", len(json_records))
        return json_records
