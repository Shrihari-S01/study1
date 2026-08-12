"""
Tests for Date Normalization & Timeline Payload Mapping.

Verifies:
1. auction_date is extracted into YYYY-MM-DD (e.g., 2026-07-24).
2. auction_start_date & start_date receive full YYYY-MM-DD HH:MM:SS timestamps.
3. auction_end_date & end_date receive full YYYY-MM-DD HH:MM:SS timestamps.
4. Inspection dates & times do NOT overwrite auction dates.
5. No zero date "0000-00-00 00:00:00" is generated anywhere in the payload.
"""

import unittest
from app.services.integration.schema_builder import CommonAISchemaBuilder
from app.services.integration.payload_mapper import PurePayloadMapper

class TestDatePayloadNormalization(unittest.TestCase):

    def test_auction_date_and_timestamps(self):
        raw_record = {
            "auction_number": "01",
            "auction_date": "24.07.2026",
            "auction_start_datetime": "2026-07-24 14:00:00",
            "auction_end_datetime": "2026-07-24 18:00:00",
            "inspection_from_date": "2026-06-22 11:00:00",
            "inspection_to_date": "2026-06-22 17:00:00"
        }

        from app.services.integration.normalizer import DataNormalizer
        schema = CommonAISchemaBuilder.build_schema(raw_record, lot_index=1)
        schema = DataNormalizer.normalize_schema(schema, lot_index=1)
        mapper = PurePayloadMapper()
        payload = mapper.map_to_php_payload(schema, lot_index=1)

        # 1. Check auction_date is YYYY-MM-DD
        self.assertEqual(payload.get("auction_date"), "2026-07-24")
        self.assertEqual(payload.get("p_auction_date"), "2026-07-24")

        # 2. Check start_date / auction_start_date contain full timestamp
        self.assertEqual(payload.get("auction_start_date"), "2026-07-24 14:00:00")
        self.assertEqual(payload.get("start_date"), "2026-07-24 14:00:00")

        # 3. Check end_date / auction_end_date contain full timestamp
        self.assertEqual(payload.get("auction_end_date"), "2026-07-24 18:00:00")
        self.assertEqual(payload.get("end_date"), "2026-07-24 18:00:00")

        # 4. Verify no zero dates
        for k, v in payload.items():
            if "date" in k:
                self.assertNotIn("0000-00-00", str(v))

    def test_explicit_end_datetime_and_geographic_location_isolation(self):
        raw_record = {
            "auction_number": "02",
            "auction_date": "2026-07-28",
            "auction_start_datetime": "2026-07-28 10:00:00",
            "auction_end_datetime": "2026-07-28 13:00:00",
            "auction_extend_time": 90,
            "property_address": "House No. 64, Mal Avenue, Tehsil Malhabad, Lucknow",
            "description": "House No. 64"
        }

        from app.services.integration.normalizer import DataNormalizer
        schema = CommonAISchemaBuilder.build_schema(raw_record, lot_index=2)
        schema = DataNormalizer.normalize_schema(schema, lot_index=2)
        mapper = PurePayloadMapper()
        payload = mapper.map_to_php_payload(schema, lot_index=2)

        # Verify all end date/time fields preserve the explicit end timestamp
        self.assertEqual(payload.get("auction_end_date"), "2026-07-28 13:00:00")
        self.assertEqual(payload.get("p_auction_end_date"), "2026-07-28 13:00:00")
        self.assertEqual(payload.get("end_date"), "2026-07-28 13:00:00")
        self.assertEqual(payload.get("p_end_date"), "2026-07-28 13:00:00")

        # Verify location contains ONLY geographic text and zero serialized object syntax
        self.assertIn("House No. 64", payload.get("property_address"))
        self.assertNotIn("[{", payload.get("property_address"))
        self.assertNotIn("item:", payload.get("property_address"))

    def test_concatenated_ocr_date_time_parsing(self):
        from app.services.extractor.parser import AuctionParser
        parser = AuctionParser()
        ocr_sample = "DATE AND TIME OF COMMENCEMENT OF E-AUCTION 24.072026FROM02:00PMTO06:00PM"
        shared = parser.extract_shared_metadata(ocr_sample)

        self.assertEqual(shared.get("auction_date"), "2026-07-24")
        self.assertEqual(shared.get("auction_start_datetime"), "2026-07-24 14:00:00")
        self.assertEqual(shared.get("auction_end_datetime"), "2026-07-24 18:00:00")
        self.assertEqual(shared.get("auction_time"), "14:00:00")
        self.assertEqual(shared.get("auction_end_time"), "18:00:00")

if __name__ == "__main__":
    unittest.main()
