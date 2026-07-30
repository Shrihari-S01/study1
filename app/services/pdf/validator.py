"""
Structural & Business Validator for PDF Processing Pipeline (Stage 11).
Strict Rejection Rules per lot before JSON serialization.
"""

from app.core.logger import get_logger

logger = get_logger(__name__)


class PDFValidator:
    """
    Validates PDF extraction results per lot record before JSON output.
    """

    PARSER_ARTIFACTS = {")", "-", "0.0", "pcb group", "(", "0", "", "none", "null"}

    def validate_single_lot(self, record: dict) -> dict:
        """
        Validate single lot record against strict rejection criteria.
        """
        errors = []

        # Rule 1: auction_identifier missing
        auc_id = str(record.get("auction_identifier") or "").strip()
        if not auc_id:
            errors.append("auction_identifier missing")

        # Rule 2: Reject auction_no == lot_no if auction_no is equal to seller or invalid
        auc_no = str(record.get("auction_no") or "").strip()
        seller_str = str(record.get("institution_seller") or "").strip()
        if auc_no and seller_str and auc_no.lower() in seller_str.lower() and len(auc_no) > 10:
            errors.append("auction_no equals seller name")

        # Rule 3: Reject category == ")" or ending with "-"
        cat = str(record.get("asset_category") or "").strip().lower()
        if not cat or cat in self.PARSER_ARTIFACTS or cat.endswith("-") or len(cat) < 2:
            errors.append(f"invalid asset_category ('{record.get('asset_category')}')")

        # Rule 4: Reject description single word (word count <= 1 or length <= 5)
        desc = str(record.get("auction_description") or "").strip()
        desc_words = desc.split()
        if not desc or len(desc) <= 5 or len(desc_words) <= 1:
            errors.append(f"description single word or too short ('{desc}')")

        # Rule 5: Reserve Price numeric
        res = record.get("reserve_price") or record.get("starting_price")
        if res is None or not isinstance(res, (int, float)):
            errors.append("reserve_price not numeric")

        # Rule 6: Increment Price numeric
        inc = record.get("increment_price")
        if inc is None or not isinstance(inc, (int, float)):
            errors.append("increment_price not numeric")

        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "errors": errors
        }

    def validate_lot_records(self, lot_records: list[dict], expected_count: int = 0) -> dict:
        """
        Perform structural and field-level validation across extracted lot records.
        """
        status = {
            "is_valid": True,
            "lot_count_match": True,
            "missing_fields_per_lot": {},
            "errors": []
        }

        if expected_count > 0 and len(lot_records) != expected_count:
            status["is_valid"] = False
            status["lot_count_match"] = False
            status["errors"].append(f"Lot Count Mismatch: Expected {expected_count} lots, but generated {len(lot_records)} output records.")
            logger.warning(status["errors"][-1])

        for idx, rec in enumerate(lot_records):
            lot_id = str(rec.get("lot_no") or idx + 1)
            v_res = self.validate_single_lot(rec)
            if not v_res["is_valid"]:
                status["is_valid"] = False
                status["missing_fields_per_lot"][lot_id] = v_res["errors"]

        return status
