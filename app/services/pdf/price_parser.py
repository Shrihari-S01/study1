"""
Price & Financial Parser for PDF Auction Processing Pipeline.
Deterministic extraction of starting_price, reserve_price, increment_price, pre_bid_emd, and post_bid_emd_percent.
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)


class PriceParser:
    """
    Extracts financial values from a lot block text without arbitrary calculation.
    """

    def parse_prices(self, text: str) -> dict:
        """
        Extract financial fields dict.
        """
        price_data = {
            "starting_price": None,
            "reserve_price": None,
            "increment_price": None,
            "pre_bid_emd": None,
            "emd_price": None,
            "post_bid_emd_percent": None,
            "sources": {}
        }

        if not text:
            return price_data

        # 1. Reserve Price / Start Price (Must come from 'Start Price in INR')
        sp_m = re.search(r'(?i)(?:Start\s+Price\s+in\s+INR|Start\s+Price|Reserve\s+Price)\s*[-:]?\s*([\d,]+(?:\.\d+)?)', text)
        if sp_m:
            try:
                val = float(sp_m.group(1).replace(",", ""))
                price_data["starting_price"] = val
                price_data["reserve_price"] = val
                price_data["sources"]["reserve_price"] = "Start Price in INR"
            except Exception:
                pass

        # 2. Bid Increment (Must come from 'Bid Increment in INR')
        inc_m = re.search(r'(?i)(?:Bid\s+Increment\s+in\s+INR|Bid\s+Increment|Minimum\s+Bid\s+Increment)\s*[-:]?\s*([\d,]+(?:\.\d+)?)', text)
        if inc_m:
            try:
                val = float(inc_m.group(1).replace(",", ""))
                price_data["increment_price"] = val
                price_data["sources"]["increment_price"] = "Bid Increment in INR"
            except Exception:
                pass

        # 3. Pre-Bid EMD Amount (Must come strictly from 'Pre-Bid EMD Amount')
        emd_m = re.search(r'(?i)(?:Pre-Bid\s+EMD(?:\s+Amount)?|EMD\s+Amount|Pre-Bid\s+EMD)\s*[-:\s]*(?:Rs\.?|INR)?\s*[:.-]?\s*([\d,]+(?:\.\d+)?)', text)
        if emd_m:
            try:
                val = float(emd_m.group(1).replace(",", ""))
                price_data["pre_bid_emd"] = val
                price_data["emd_price"] = val
                price_data["sources"]["emd_price"] = "Pre-Bid EMD Amount"
            except Exception:
                pass

        # 4. Post Bid EMD Percentage (Does NOT map to emd_price)
        pct_m = re.search(r'(?i)(?:Post\s+Bid\s+EMD\s*%|EMD\s*%|EMD\s+Percentage)\s*[-:]?\s*(\d+(?:\.\d+)?)', text)
        if pct_m:
            try:
                price_data["post_bid_emd_percent"] = float(pct_m.group(1))
            except Exception:
                pass

        return price_data
