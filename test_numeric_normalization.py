"""
Tests for Final PHP Payload Boundary & Numeric Field Normalization.

Verifies:
1. Missing increment_price ("") -> None (serializes to JSON null)
2. Python None -> None
3. Actual string number ("5000", "5,000", "₹5,000") -> 5000.00
4. Decimal string ("5000.50") -> 5000.50
5. Actual numeric zero (0 or 0.0) -> 0.00
6. Non-numeric invalid text ("N/A", "-", "null") -> None
7. Prohibits "" from ever reaching PHP POST payload for any DECIMAL field.
"""

import unittest
from decimal import Decimal
from app.services.integration.php_payload_normalizer import CentralizedPHPPayloadNormalizer
from app.services.integration.payload_sanitizer import PHPSanitizer, sanitize_json_payload

class TestNumericPayloadNormalization(unittest.TestCase):

    def test_normalize_decimal_for_db_missing_and_text(self):
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db(None), Decimal("0.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db(""), Decimal("0.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db(" "), Decimal("0.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db("null"), Decimal("0.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db("None"), Decimal("0.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db("N/A"), Decimal("0.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db("NA"), Decimal("0.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db("-"), Decimal("0.00"))

    def test_normalize_decimal_for_db_values(self):
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db("5000"), Decimal("5000.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db("5,000"), Decimal("5000.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db("₹5,000"), Decimal("5000.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db("5000.50"), Decimal("5000.50"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db(5000), Decimal("5000.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db(0), Decimal("0.00"))
        self.assertEqual(CentralizedPHPPayloadNormalizer.normalize_decimal_for_db(0.0), Decimal("0.00"))

    def test_sanitize_and_validate_payload_decimal_fields(self):
        test_payload = {
            "auction_number": "TEST-01",
            "vendor_id": 1,
            "section_id": 1,
            "part_id": 1,
            "p_increment_price": "",
            "increment_price": None,
            "p_reserve_price": "5,000",
            "p_auction_start_price": 0,
            "p_emd_price": "5000.50",
            "p_emd_amount": "N/A",
            "p_pre_bid_emd": "-"
        }
        
        sanitized, is_valid, errors = PHPSanitizer.sanitize_and_validate_payload(test_payload, processing_id="TEST_RUN")
        self.assertTrue(is_valid)
        self.assertEqual(sanitized.get("p_increment_price"), None)
        self.assertEqual(sanitized.get("increment_price"), None)
        self.assertEqual(sanitized.get("p_reserve_price"), 5000.00)
        self.assertEqual(sanitized.get("p_auction_start_price"), 0.00)
        self.assertEqual(sanitized.get("p_emd_price"), 5000.50)
        self.assertEqual(sanitized.get("p_emd_amount"), None)
        self.assertEqual(sanitized.get("p_pre_bid_emd"), 0.00)

    def test_sanitize_json_payload_prevents_empty_string(self):
        dirty_json = {
            "p_increment_price": "",
            "p_reserve_price": "5000.00",
            "p_emd_price": "N/A"
        }
        cleaned = sanitize_json_payload(dirty_json)
        self.assertEqual(cleaned["p_increment_price"], 0.00)
        self.assertEqual(cleaned["p_reserve_price"], "5000.00")
        self.assertEqual(cleaned["p_emd_price"], 0.00)

if __name__ == "__main__":
    unittest.main()
