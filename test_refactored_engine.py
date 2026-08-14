"""
Regression unit test for strict 22-step auction extraction refactor engine.
"""

import unittest
from app.services.extractor.refactored_extraction_engine import StrictAuctionRefactorEngine

class TestStrictAuctionRefactorEngine(unittest.TestCase):

    def setUp(self):
        self.engine = StrictAuctionRefactorEngine()

    def test_multi_auction_extraction(self):
        # Synthetic OCR tokens containing 2 distinct auctions:
        # Auction 1: Plant & Machinery
        # Auction 2: Land & Building
        sample_ocr_data = [
            # Header & Seller
            {"text": "CANARA", "confidence": 0.99, "bbox": [50, 20, 120, 40]},
            {"text": "BANK", "confidence": 0.99, "bbox": [125, 20, 180, 40]},
            {"text": "E-AUCTION", "confidence": 0.98, "bbox": [200, 20, 300, 40]},
            {"text": "SALE", "confidence": 0.98, "bbox": [305, 20, 350, 40]},
            {"text": "NOTICE", "confidence": 0.98, "bbox": [355, 20, 410, 40]},

            # Borrower
            {"text": "Borrower:", "confidence": 0.95, "bbox": [50, 60, 130, 80]},
            {"text": "M/s", "confidence": 0.95, "bbox": [140, 60, 170, 80]},
            {"text": "Fineline", "confidence": 0.95, "bbox": [175, 60, 240, 80]},
            {"text": "Food", "confidence": 0.95, "bbox": [245, 60, 290, 80]},
            {"text": "And", "confidence": 0.95, "bbox": [295, 60, 330, 80]},
            {"text": "Beverages", "confidence": 0.95, "bbox": [335, 60, 420, 80]},
            {"text": "Private", "confidence": 0.95, "bbox": [425, 60, 480, 80]},
            {"text": "Limited", "confidence": 0.95, "bbox": [485, 60, 550, 80]},
            {"text": "(Borrower)", "confidence": 0.90, "bbox": [555, 60, 630, 80]},

            # Candidate 1: Plant & Machinery
            {"text": "DESCRIPTION", "confidence": 0.95, "bbox": [50, 120, 150, 140]},
            {"text": "OF", "confidence": 0.95, "bbox": [155, 120, 175, 140]},
            {"text": "PLANT", "confidence": 0.95, "bbox": [180, 120, 230, 140]},
            {"text": "&", "confidence": 0.95, "bbox": [235, 120, 245, 140]},
            {"text": "MACHINERY", "confidence": 0.95, "bbox": [250, 120, 340, 140]},
            {"text": "Reserve", "confidence": 0.95, "bbox": [50, 150, 110, 170]},
            {"text": "Price:", "confidence": 0.95, "bbox": [115, 150, 160, 170]},
            {"text": "3,91,77,800/", "confidence": 0.96, "bbox": [165, 150, 280, 170]},
            {"text": "EMD:", "confidence": 0.95, "bbox": [50, 180, 90, 200]},
            {"text": "39,17,780/", "confidence": 0.95, "bbox": [100, 180, 190, 200]},

            # Candidate 2: Land & Building (Child Property Protection)
            {"text": "DESCRIPTION", "confidence": 0.95, "bbox": [50, 300, 150, 320]},
            {"text": "OF", "confidence": 0.95, "bbox": [155, 300, 175, 320]},
            {"text": "LAND", "confidence": 0.95, "bbox": [180, 300, 220, 320]},
            {"text": "&", "confidence": 0.95, "bbox": [225, 300, 235, 320]},
            {"text": "BUILDING", "confidence": 0.95, "bbox": [240, 300, 320, 320]},
            {"text": "Property", "confidence": 0.92, "bbox": [50, 330, 110, 350]},
            {"text": "No.1", "confidence": 0.92, "bbox": [115, 330, 150, 350]},
            {"text": "Plot", "confidence": 0.92, "bbox": [155, 330, 190, 350]},
            {"text": "No.", "confidence": 0.92, "bbox": [195, 330, 220, 350]},
            {"text": "64,", "confidence": 0.92, "bbox": [225, 330, 250, 350]},
            {"text": "Lucknow", "confidence": 0.95, "bbox": [255, 330, 320, 350]},
            {"text": "Reserve", "confidence": 0.95, "bbox": [50, 360, 110, 380]},
            {"text": "Price:", "confidence": 0.95, "bbox": [115, 360, 160, 380]},
            {"text": "1,50,00,000/", "confidence": 0.96, "bbox": [165, 360, 280, 380]},
            {"text": "EMD:", "confidence": 0.95, "bbox": [50, 390, 90, 410]},
            {"text": "15,00,000/", "confidence": 0.95, "bbox": [100, 390, 180, 410]}
        ]

        res = self.engine.run_extraction(sample_ocr_data, image_name="test_notice.png")

        self.assertTrue(res["success"])
        self.assertEqual(res["detected_candidates"], 2)
        self.assertEqual(res["final_records_count"], 2)
        self.assertEqual(len(res["records"]), 2)

        # Assert no hardcoded '01' fallback
        rec1 = res["records"][0]
        rec2 = res["records"][1]

        self.assertEqual(rec1["asset_type"], "Movable")
        self.assertEqual(rec1["asset_category"], "Plant & Machinery")
        self.assertEqual(rec1["reserve_price"], 39177800.0)

        self.assertEqual(rec2["asset_type"], "Immovable")
        self.assertEqual(rec2["asset_category"], "Land & Building")
        self.assertEqual(rec2["reserve_price"], 15000000.0)

    def test_ocr_adapter_integrity(self):
        from app.services.ocr.ocr_adapter import parse_paddleocr_result
        # Sample PaddleOCR format: [ [[[x1,y1],[x2,y2],[x3,y3],[x4,y4]], (text, conf)] ]
        sample_paddle_raw = [
            [
                [[[10, 10], [100, 10], [100, 30], [10, 30]], ("CANARA BANK", 0.99)],
                [[[10, 40], [200, 40], [200, 60], [10, 60]], ("E-AUCTION SALE NOTICE", 0.98)],
                [[[10, 70], [300, 70], [300, 90], [10, 90]], ("Borrower: M/s Fineline Food", 0.95)],
            ]
        ]
        tokens = parse_paddleocr_result(sample_paddle_raw)
        self.assertEqual(len(tokens), 3)
        self.assertEqual(tokens[0].text, "CANARA BANK")
        self.assertEqual(tokens[1].text, "E-AUCTION SALE NOTICE")
        self.assertEqual(tokens[2].text, "Borrower: M/s Fineline Food")

    def test_adapter_error_handling(self):
        from app.services.ocr.ocr_adapter import parse_paddleocr_result
        with self.assertRaises(ValueError):
            parse_paddleocr_result([])

if __name__ == "__main__":
    unittest.main()
