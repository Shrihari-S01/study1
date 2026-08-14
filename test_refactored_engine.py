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

    def test_six_lot_lic_notice(self):
        sample_lic_ocr = [
            # Header
            {"text": "LIC HOUSING FINANCE LTD.", "confidence": 0.99, "bbox": [50, 10, 300, 30]},
            {"text": "E-AUCTION SALE NOTICE", "confidence": 0.99, "bbox": [50, 35, 250, 55]},
            {"text": "E Auction Date: 22nd July 2026 11 AM TO 1 PM", "confidence": 0.98, "bbox": [50, 60, 400, 80]},
            {"text": "Last date of submission of Online Tender/Bid: 21st July 2026 - 5 PM", "confidence": 0.98, "bbox": [50, 85, 450, 105]},

            # Lot 1
            {"text": "Sl.No.1", "confidence": 0.99, "bbox": [50, 120, 100, 140]},
            {"text": "Borrower Name: MRS. KATHIRVEL & MS. K. KAVITHA", "confidence": 0.98, "bbox": [110, 120, 500, 140]},
            {"text": "Loan No. 71180000123", "confidence": 0.95, "bbox": [50, 145, 200, 165]},
            {"text": "DESCRIPTION OF THE PROPERTY Schedule-A Land & Building in Tambaram, Kancheepuram, Tamil Nadu", "confidence": 0.95, "bbox": [50, 170, 700, 190]},
            {"text": "Reserve Price - Rs. 40,00,000/-", "confidence": 0.98, "bbox": [50, 195, 250, 215]},
            {"text": "EMD - Rs. 4,00,000/-", "confidence": 0.98, "bbox": [260, 195, 400, 215]},

            # Lot 2
            {"text": "Sl.No.2", "confidence": 0.99, "bbox": [50, 240, 100, 260]},
            {"text": "Borrower Name: MRS. KATHIRVEL & MS. K. KAVITHA", "confidence": 0.98, "bbox": [110, 240, 500, 260]},
            {"text": "Loan No. 71180000124", "confidence": 0.95, "bbox": [50, 265, 200, 285]},
            {"text": "DESCRIPTION OF THE PROPERTY Schedule-A Flat in Pallikaranai, Chennai, Tamil Nadu", "confidence": 0.95, "bbox": [50, 290, 700, 310]},
            {"text": "Reserve Price - Rs. 37,00,000/-", "confidence": 0.98, "bbox": [50, 315, 250, 335]},
            {"text": "EMD - Rs. 3,70,000/-", "confidence": 0.98, "bbox": [260, 315, 400, 335]},

            # Lot 3
            {"text": "Sl.No.3", "confidence": 0.99, "bbox": [50, 360, 100, 380]},
            {"text": "Borrower Name: MR. K. SRINIVASAN", "confidence": 0.98, "bbox": [110, 360, 450, 380]},
            {"text": "Loan No. 71180000125", "confidence": 0.95, "bbox": [50, 385, 200, 405]},
            {"text": "DESCRIPTION OF THE PROPERTY Schedule-A Property in Sholinganallur, Chennai", "confidence": 0.95, "bbox": [50, 410, 700, 430]},
            {"text": "Reserve Price - Rs. 22,50,000/-", "confidence": 0.98, "bbox": [50, 435, 250, 455]},
            {"text": "EMD - Rs. 2,25,000/-", "confidence": 0.98, "bbox": [260, 435, 400, 455]},

            # Lot 4
            {"text": "Sl.No.4", "confidence": 0.99, "bbox": [50, 480, 100, 500]},
            {"text": "Borrower Name: MR. VINOD S.P.", "confidence": 0.98, "bbox": [110, 480, 400, 500]},
            {"text": "Loan No. 71180000126", "confidence": 0.95, "bbox": [50, 505, 200, 525]},
            {"text": "DESCRIPTION OF THE PROPERTY Schedule-A Land & Building in Madambakkam, Chengalpattu", "confidence": 0.95, "bbox": [50, 530, 700, 550]},
            {"text": "Reserve Price - Rs. 30,00,000/-", "confidence": 0.98, "bbox": [50, 555, 250, 575]},
            {"text": "EMD - Rs. 3,00,000/-", "confidence": 0.98, "bbox": [260, 555, 400, 575]},

            # Lot 5
            {"text": "Sl.No.5", "confidence": 0.99, "bbox": [50, 600, 100, 620]},
            {"text": "Borrower Name: MRS. SRIDEVI & MR. D. SENTHIL KUMAR", "confidence": 0.98, "bbox": [110, 600, 550, 620]},
            {"text": "Loan No. 71180000127", "confidence": 0.95, "bbox": [50, 625, 200, 645]},
            {"text": "DESCRIPTION OF THE PROPERTY Schedule-A Flat in Sriperumbudur, Kancheepuram", "confidence": 0.95, "bbox": [50, 650, 700, 670]},
            {"text": "Reserve Price - Rs. 45,00,000/-", "confidence": 0.98, "bbox": [50, 675, 250, 695]},
            {"text": "EMD - Rs. 4,50,000/-", "confidence": 0.98, "bbox": [260, 675, 400, 695]},

            # Lot 6
            {"text": "Sl.No.6", "confidence": 0.99, "bbox": [50, 720, 100, 740]},
            {"text": "Borrower Name: MR. P. GIRIDHARAN", "confidence": 0.98, "bbox": [110, 720, 450, 740]},
            {"text": "Loan No. 71180000128", "confidence": 0.95, "bbox": [50, 745, 200, 765]},
            {"text": "DESCRIPTION OF THE PROPERTY Schedule-A House Property in Chennai, Tamil Nadu", "confidence": 0.95, "bbox": [50, 770, 700, 790]},
            {"text": "Reserve Price - Rs. 30,00,000/-", "confidence": 0.98, "bbox": [50, 795, 250, 815]},
            {"text": "EMD - Rs. 3,00,000/-", "confidence": 0.98, "bbox": [260, 795, 400, 815]}
        ]

        res = self.engine.run_extraction(sample_lic_ocr, image_name="lic_notice.png")

        self.assertTrue(res["success"])
        self.assertEqual(res["detected_candidates"], 6)
        self.assertEqual(res["final_records_count"], 6)
        self.assertEqual(len(res["records"]), 6)

        recs = res["records"]
        # Check auction numbers 01..06
        self.assertEqual([r.get("auction_no") for r in recs], ["01", "02", "03", "04", "05", "06"])

        # Check Seller
        for r in recs:
            self.assertTrue(r.get("institution_seller", "").startswith("LIC HOUSING FINANCE"))
            self.assertEqual(r.get("auction_date"), "2026-07-22")
            self.assertEqual(r.get("submit_application"), "2026-07-21 17:00:00")
            self.assertEqual(r.get("asset_type"), "Immovable")

        # Check Borrower Name Isolation
        self.assertIn("KATHIRVEL & MS. K. KAVITHA", recs[0]["borrower_name"])
        self.assertIn("KATHIRVEL & MS. K. KAVITHA", recs[1]["borrower_name"])
        self.assertEqual(recs[2]["borrower_name"], "MR. K. SRINIVASAN")
        self.assertEqual(recs[3]["borrower_name"], "MR. VINOD S.P.")
        self.assertIn("SRIDEVI & MR. D. SENTHIL KUMAR", recs[4]["borrower_name"])
        self.assertEqual(recs[5]["borrower_name"], "MR. P. GIRIDHARAN")

        # Check Reserve Prices
        self.assertEqual(recs[0]["reserve_price"], 4000000.0)
        self.assertEqual(recs[1]["reserve_price"], 3700000.0)
        self.assertEqual(recs[2]["reserve_price"], 2250000.0)
        self.assertEqual(recs[3]["reserve_price"], 3000000.0)
        self.assertEqual(recs[4]["reserve_price"], 4500000.0)
        self.assertEqual(recs[5]["reserve_price"], 3000000.0)

        # Check EMD Amounts
        self.assertEqual(recs[0]["emd_price"], 400000.0)
        self.assertEqual(recs[1]["emd_price"], 370000.0)
        self.assertEqual(recs[2]["emd_price"], 225000.0)
        self.assertEqual(recs[3]["emd_price"], 300000.0)
        self.assertEqual(recs[4]["emd_price"], 450000.0)
        self.assertEqual(recs[5]["emd_price"], 300000.0)

    def test_twenty_auction_grid_notice(self):
        sample_20_ocr = [
            {"text": "STATE BANK OF INDIA", "confidence": 0.99, "bbox": [50, 10, 300, 30]},
            {"text": "MEGA E-AUCTION SALE NOTICE", "confidence": 0.99, "bbox": [50, 35, 350, 55]},
        ]

        # Generate 20 auctions across 2 columns (Column 1: X=50..400, Column 2: X=500..900)
        # Column 1: Sl.No. 1 to 10
        for i in range(1, 11):
            y_base = 80 + (i - 1) * 70
            sample_20_ocr.extend([
                {"text": f"Sl.No.{i}", "confidence": 0.99, "bbox": [50, y_base, 100, y_base + 20]},
                {"text": f"Borrower: Borrower_{i}", "confidence": 0.95, "bbox": [110, y_base, 350, y_base + 20]},
                {"text": f"Amt Demanded: Rs 15,{i:02d},000/-", "confidence": 0.95, "bbox": [50, y_base + 22, 300, y_base + 40]},
                {"text": f"Reserve Price: Rs 50,{i:02d},000/-", "confidence": 0.98, "bbox": [50, y_base + 42, 250, y_base + 60]},
                {"text": f"EMD: Rs 5,{i:02d},000/-", "confidence": 0.98, "bbox": [260, y_base + 42, 400, y_base + 60]},
            ])

        # Column 2: Sl.No. 11 to 20
        for i in range(11, 21):
            y_base = 80 + (i - 11) * 70
            sample_20_ocr.extend([
                {"text": f"Sl.No.{i}", "confidence": 0.99, "bbox": [500, y_base, 550, y_base + 20]},
                {"text": f"Borrower: Borrower_{i}", "confidence": 0.95, "bbox": [560, y_base, 850, y_base + 20]},
                {"text": f"Amt Demanded: Rs 15,{i:02d},000/-", "confidence": 0.95, "bbox": [500, y_base + 22, 750, y_base + 40]},
                {"text": f"Reserve Price: Rs 50,{i:02d},000/-", "confidence": 0.98, "bbox": [500, y_base + 42, 700, y_base + 60]},
                {"text": f"EMD: Rs 5,{i:02d},000/-", "confidence": 0.98, "bbox": [710, y_base + 42, 880, y_base + 60]},
            ])

        res = self.engine.run_extraction(sample_20_ocr, image_name="twenty_auction_notice.png")

        self.assertTrue(res["success"])
        self.assertEqual(res["detected_candidates"], 20)
        self.assertEqual(res["final_records_count"], 20)
        self.assertEqual(len(res["records"]), 20)

        recs = res["records"]
        for idx, rec in enumerate(recs, start=1):
            expected_bor = f"Borrower_{idx}"
            self.assertIn(expected_bor, rec["borrower_name"])

            # Verify Reserve Price is 50,XX,000 and NEVER 15,XX,000 (demand amount)
            res_val = rec["reserve_price"]
            self.assertIsNotNone(res_val)
            self.assertTrue(res_val >= 5000000.0)
            self.assertNotEqual(res_val, 1500000.0 + idx * 1000.0)

    def test_metadata_account_inspection_fields(self):
        sample_meta_ocr = [
            {"text": "LIC HOUSING FINANCE LTD", "confidence": 0.99, "bbox": [50, 10, 300, 30]},
            {"text": "Branch Office: Chennai Back Office", "confidence": 0.95, "bbox": [50, 35, 350, 55]},
            {"text": "Asset Recovery Department", "confidence": 0.95, "bbox": [50, 60, 300, 80]},

            # Auction 1
            {"text": "Sl.No.1", "confidence": 0.99, "bbox": [50, 100, 100, 120]},
            {"text": "Borrower Name: Mr. S. Kathirvel", "confidence": 0.95, "bbox": [110, 100, 350, 120]},
            {"text": "Reserve Price: Rs 40,00,000/-", "confidence": 0.98, "bbox": [50, 125, 250, 145]},
            {"text": "EMD: Rs 4,00,000/-", "confidence": 0.98, "bbox": [260, 125, 400, 145]},
            {"text": "Beneficiary Name: LIC Housing Finance Ltd.", "confidence": 0.95, "bbox": [50, 150, 400, 170]},
            {"text": "Bank: Axis Bank", "confidence": 0.95, "bbox": [50, 175, 180, 195]},
            {"text": "Account No: LHMA510500002356", "confidence": 0.95, "bbox": [190, 175, 420, 195]},
            {"text": "IFSC Code: UTIBOCCH274", "confidence": 0.95, "bbox": [430, 175, 600, 195]},
            {"text": "Authorized Officer: Mr. Ashok G.", "confidence": 0.95, "bbox": [50, 200, 320, 220]},
            {"text": "Officer Contact: 9876543210", "confidence": 0.95, "bbox": [330, 200, 520, 220]},
            {"text": "Payment Mode: NEFT/RTGS", "confidence": 0.95, "bbox": [50, 225, 250, 245]},
            {"text": "Inspection of Photo copies of property documents: 20th July 2026 between 11.00 AM and 3.00 PM", "confidence": 0.95, "bbox": [50, 250, 800, 270]},

            # Auction 2
            {"text": "Sl.No.2", "confidence": 0.99, "bbox": [50, 300, 100, 320]},
            {"text": "Borrower Name: Mr. K. Srinivasan", "confidence": 0.95, "bbox": [110, 300, 350, 320]},
            {"text": "Reserve Price: Rs 22,50,000/-", "confidence": 0.98, "bbox": [50, 325, 250, 345]},
            {"text": "EMD: Rs 2,25,000/-", "confidence": 0.98, "bbox": [260, 325, 400, 345]},
            {"text": "Beneficiary Name: LIC Housing Finance Ltd.", "confidence": 0.95, "bbox": [50, 350, 400, 370]},
            {"text": "Bank: Canara Bank", "confidence": 0.95, "bbox": [50, 375, 180, 395]},
            {"text": "Account No: LHMA510500006179", "confidence": 0.95, "bbox": [190, 375, 420, 395]},
            {"text": "IFSC Code: CNRB0001234", "confidence": 0.95, "bbox": [430, 375, 600, 395]},
        ]

        res = self.engine.run_extraction(sample_meta_ocr, image_name="meta_test_notice.png")

        self.assertTrue(res["success"])
        self.assertEqual(res["final_records_count"], 2)
        recs = res["records"]

        # Check Auction 1 Metadata
        r1 = recs[0]
        self.assertEqual(r1.get("emd_bank_name"), "Axis Bank")
        self.assertEqual(r1.get("emd_account_no"), "LHMA510500002356")
        self.assertEqual(r1.get("emd_ifsc"), "UTIB0CCH274")  # 5th char 'O' normalized to '0'
        self.assertIn("Ashok", r1.get("authorized_officer_name", ""))
        self.assertEqual(r1.get("authorized_officer_number"), "9876543210")
        self.assertEqual(r1.get("payment_type"), "NEFT/RTGS")
        self.assertEqual(r1.get("inspection_from_date"), "20th July 2026 11:00 AM")
        self.assertEqual(r1.get("inspection_to_date"), "20th July 2026 3:00 PM")

        # Check Auction 2 Metadata & Cross-Auction Isolation
        r2 = recs[1]
        self.assertEqual(r2.get("emd_bank_name"), "Canara Bank")
        self.assertEqual(r2.get("emd_account_no"), "LHMA510500006179")
        self.assertEqual(r2.get("emd_ifsc"), "CNRB0001234")
        self.assertNotEqual(r2.get("emd_account_no"), r1.get("emd_account_no"))

    def test_merged_auction_headers_are_detected(self):
        from app.services.extractor.refactored_extraction_engine import (
            OCRToken, detect_auction_anchors, deduplicate_auction_anchors
        )
        sample_merged_ocr = [
            OCRToken(id=1, text="SLNo.1BorrwerName:MR.S.KATHIRVEL-LoanNo-511400001030-Reserve Price: Rs 40,00,000/- EMD: Rs 4,00,000/-", normalized_text="SLNo.1BorrwerName:MR.S.KATHIRVEL-LoanNo-511400001030-Reserve Price: Rs 40,00,000/- EMD: Rs 4,00,000/-", confidence=0.95, bbox=(10, 10, 600, 35), x1=10, y1=10, x2=600, y2=35, center_x=305, center_y=22.5),
            OCRToken(id=2, text="SL.N0.2:B0rr0werName:MRS.KATHIRVEL-LoanNo-511400001029-Reserve Price: Rs 37,00,000/- EMD: Rs 3,70,000/-", normalized_text="SL.N0.2:B0rr0werName:MRS.KATHIRVEL-LoanNo-511400001029-Reserve Price: Rs 37,00,000/- EMD: Rs 3,70,000/-", confidence=0.95, bbox=(10, 100, 600, 125), x1=10, y1=100, x2=600, y2=125, center_x=305, center_y=112.5),
            OCRToken(id=3, text="Sl.No.3:BorrowerName: Mr.K.Srinivasan-Loan No-510600007566-Reserve Price: Rs 22,50,000/- EMD: Rs 2,25,000/-", normalized_text="Sl.No.3:BorrowerName: Mr.K.Srinivasan-Loan No-510600007566-Reserve Price: Rs 22,50,000/- EMD: Rs 2,25,000/-", confidence=0.95, bbox=(10, 200, 600, 225), x1=10, y1=200, x2=600, y2=225, center_x=305, center_y=212.5),
            OCRToken(id=4, text="SLNo.4Borrower Name:MrVinodS.P.-Loan No-510590003980-Reserve Price: Rs 30,00,000/- EMD: Rs 3,00,000/-", normalized_text="SLNo.4Borrower Name:MrVinodS.P.-Loan No-510590003980-Reserve Price: Rs 30,00,000/- EMD: Rs 3,00,000/-", confidence=0.95, bbox=(10, 300, 600, 325), x1=10, y1=300, x2=600, y2=325, center_x=305, center_y=312.5),
            OCRToken(id=5, text="SI.No.5:Borrower Name:MRS.SRIDEVIS&MR.DSENTHILKUMAR-Loan No-510500006179-Reserve Price: Rs 45,00,000/- EMD: Rs 4,50,000/-", normalized_text="SI.No.5:Borrower Name:MRS.SRIDEVIS&MR.DSENTHILKUMAR-Loan No-510500006179-Reserve Price: Rs 45,00,000/- EMD: Rs 4,50,000/-", confidence=0.95, bbox=(10, 400, 600, 425), x1=10, y1=400, x2=600, y2=425, center_x=305, center_y=412.5),
            OCRToken(id=6, text="SL.No.6Borrower Name:MR.PGIRIDHARAN-Loan No-510500002356-Reserve Price: Rs 30,00,000/- EMD: Rs 3,00,000/-", normalized_text="SL.No.6Borrower Name:MR.PGIRIDHARAN-Loan No-510500002356-Reserve Price: Rs 30,00,000/- EMD: Rs 3,00,000/-", confidence=0.95, bbox=(10, 500, 600, 525), x1=10, y1=500, x2=600, y2=525, center_x=305, center_y=512.5),
        ]

        anchors = detect_auction_anchors(sample_merged_ocr)
        anchors = deduplicate_auction_anchors(anchors)
        numbers = [a.number for a in anchors]
        self.assertEqual(numbers, [1, 2, 3, 4, 5, 6])

    def test_item_property_descriptions_are_rejected(self):
        from app.services.extractor.refactored_extraction_engine import (
            OCRToken, detect_auction_anchors
        )
        fake_tokens = [
            OCRToken(id=1, text="Item 13223.50Sq.ft Land and Building Reserve Price Rs 50,00,000/-", normalized_text="Item 13223.50Sq.ft Land and Building Reserve Price Rs 50,00,000/-", confidence=0.95, bbox=(10, 10, 500, 30), x1=10, y1=10, x2=500, y2=30, center_x=255, center_y=20),
            OCRToken(id=2, text="Item 2:432 Sq.ft Commercial Shop Reserve Price Rs 20,00,000/-", normalized_text="Item 2:432 Sq.ft Commercial Shop Reserve Price Rs 20,00,000/-", confidence=0.95, bbox=(10, 40, 500, 60), x1=10, y1=40, x2=500, y2=60, center_x=255, center_y=50),
            OCRToken(id=3, text="Survey No.276/6 Extent 2.50 Acres", normalized_text="Survey No.276/6 Extent 2.50 Acres", confidence=0.95, bbox=(10, 70, 500, 90), x1=10, y1=70, x2=500, y2=90, center_x=255, center_y=80),
            OCRToken(id=4, text="Plot No.36 Industrial Estate", normalized_text="Plot No.36 Industrial Estate", confidence=0.95, bbox=(10, 100, 500, 120), x1=10, y1=100, x2=500, y2=120, center_x=255, center_y=110),
            OCRToken(id=5, text="No.30/1A Main Road City Center", normalized_text="No.30/1A Main Road City Center", confidence=0.95, bbox=(10, 130, 500, 150), x1=10, y1=130, x2=500, y2=150, center_x=255, center_y=140),
            OCRToken(id=6, text="Schedule-A Property Details", normalized_text="Schedule-A Property Details", confidence=0.95, bbox=(10, 160, 500, 180), x1=10, y1=160, x2=500, y2=180, center_x=255, center_y=170),
            OCRToken(id=7, text="Schedule-B Property Details", normalized_text="Schedule-B Property Details", confidence=0.95, bbox=(10, 190, 500, 210), x1=10, y1=190, x2=500, y2=210, center_x=255, center_y=200),
        ]
        anchors = detect_auction_anchors(fake_tokens)
        self.assertEqual(anchors, [])

    def test_mixed_real_headers_and_item_descriptions(self):
        from app.services.extractor.refactored_extraction_engine import (
            OCRToken, detect_auction_anchors, deduplicate_auction_anchors
        )
        mixed_tokens = [
            OCRToken(id=1, text="SLNo.1BorrwerName:MR.S.KATHIRVEL-LoanNo-511400001030-Reserve Price: Rs 40,00,000/- EMD: Rs 4,00,000/-", normalized_text="SLNo.1BorrwerName:MR.S.KATHIRVEL-LoanNo-511400001030-Reserve Price: Rs 40,00,000/- EMD: Rs 4,00,000/-", confidence=0.95, bbox=(10, 10, 600, 35), x1=10, y1=10, x2=600, y2=35, center_x=305, center_y=22.5),
            OCRToken(id=2, text="Item 13223.50Sq.ft Land and Building Reserve Price Rs 50,00,000/-", normalized_text="Item 13223.50Sq.ft Land and Building Reserve Price Rs 50,00,000/-", confidence=0.95, bbox=(10, 45, 600, 70), x1=10, y1=45, x2=600, y2=70, center_x=305, center_y=57.5),
            OCRToken(id=3, text="SL.N0.2:B0rr0werName:MRS.KATHIRVEL-LoanNo-511400001029-Reserve Price: Rs 37,00,000/- EMD: Rs 3,70,000/-", normalized_text="SL.N0.2:B0rr0werName:MRS.KATHIRVEL-LoanNo-511400001029-Reserve Price: Rs 37,00,000/- EMD: Rs 3,70,000/-", confidence=0.95, bbox=(10, 100, 600, 125), x1=10, y1=100, x2=600, y2=125, center_x=305, center_y=112.5),
            OCRToken(id=4, text="Item 2:432 Sq.ft Commercial Shop Reserve Price Rs 20,00,000/-", normalized_text="Item 2:432 Sq.ft Commercial Shop Reserve Price Rs 20,00,000/-", confidence=0.95, bbox=(10, 135, 600, 160), x1=10, y1=135, x2=600, y2=160, center_x=305, center_y=147.5),
            OCRToken(id=5, text="Sl.No.3:BorrowerName: Mr.K.Srinivasan-Loan No-510600007566-Reserve Price: Rs 22,50,000/- EMD: Rs 2,25,000/-", normalized_text="Sl.No.3:BorrowerName: Mr.K.Srinivasan-Loan No-510600007566-Reserve Price: Rs 22,50,000/- EMD: Rs 2,25,000/-", confidence=0.95, bbox=(10, 200, 600, 225), x1=10, y1=200, x2=600, y2=225, center_x=305, center_y=212.5),
            OCRToken(id=6, text="SLNo.4Borrower Name:MrVinodS.P.-Loan No-510590003980-Reserve Price: Rs 30,00,000/- EMD: Rs 3,00,000/-", normalized_text="SLNo.4Borrower Name:MrVinodS.P.-Loan No-510590003980-Reserve Price: Rs 30,00,000/- EMD: Rs 3,00,000/-", confidence=0.95, bbox=(10, 300, 600, 325), x1=10, y1=300, x2=600, y2=325, center_x=305, center_y=312.5),
            OCRToken(id=7, text="SI.No.5:Borrower Name:MRS.SRIDEVIS&MR.DSENTHILKUMAR-Loan No-510500006179-Reserve Price: Rs 45,00,000/- EMD: Rs 4,50,000/-", normalized_text="SI.No.5:Borrower Name:MRS.SRIDEVIS&MR.DSENTHILKUMAR-Loan No-510500006179-Reserve Price: Rs 45,00,000/- EMD: Rs 4,50,000/-", confidence=0.95, bbox=(10, 400, 600, 425), x1=10, y1=400, x2=600, y2=425, center_x=305, center_y=412.5),
            OCRToken(id=8, text="SL.No.6Borrower Name:MR.PGIRIDHARAN-Loan No-510500002356-Reserve Price: Rs 30,00,000/- EMD: Rs 3,00,000/-", normalized_text="SL.No.6Borrower Name:MR.PGIRIDHARAN-Loan No-510500002356-Reserve Price: Rs 30,00,000/- EMD: Rs 3,00,000/-", confidence=0.95, bbox=(10, 500, 600, 525), x1=10, y1=500, x2=600, y2=525, center_x=305, center_y=512.5),
        ]
        anchors = detect_auction_anchors(mixed_tokens)
        anchors = deduplicate_auction_anchors(anchors)
        numbers = [a.number for a in anchors]
        self.assertEqual(numbers, [1, 2, 3, 4, 5, 6])

if __name__ == "__main__":
    unittest.main()
