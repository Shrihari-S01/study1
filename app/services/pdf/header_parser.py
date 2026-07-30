"""
Header Parser for PDF Auction Processing Pipeline.
Extracts shared notice metadata, auction identifier, auction number, assets location, dates, EMD amount, and currency.
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)


def safe_print(msg: str):
    try:
        print(msg)
    except Exception:
        pass


class HeaderParser:
    """
    Extracts shared notice metadata from the Header section.
    """

    def parse_header(self, text: str, full_pdf_text: str = "") -> dict:
        """
        Extract shared metadata dict.
        """
        shared = {
            "auction_identifier": None,
            "auction_no": None,
            "assets_location": None,
            "catalogue_view_date": None,
            "inspection_schedule_from_date": None,
            "inspection_schedule_to_date": None,
            "auction_date_time": None,
            "auction_end_date_time": None,
            "pre_bid_emd_amount": None,
            "currency": "INR",
            "auction_type": "Forward",
            "auto_extension": None,
            "auction_extend_time": None
        }

        if not text and not full_pdf_text:
            return shared

        # 1. Multi-line Auction Identifier & Numeric Auction Number
        # Example: Auction Number: MSTC/SRO/BSNL,TRICHY/13/TRICHY/26-27/20294
        auc_num_m = re.search(r'(?i)(?:Auction\s+Number|Auction\s+No|Notice\s+No|E-Auction\s+No)\s*[:.-]?\s*([\s\S]*?)(?=Auction\s+Type|Catalogue\s+View|Inspection|Scheduled|$)', text)
        if auc_num_m:
            raw_ident_lines = [ln.strip() for ln in auc_num_m.group(1).splitlines() if ln.strip()]
            raw_ident = " ".join(raw_ident_lines)
            raw_ident = re.sub(r'\s+', ' ', raw_ident).strip()
            shared["auction_identifier"] = raw_ident

            digits_m = re.findall(r'\d+', raw_ident)
            if digits_m:
                shared["auction_no"] = digits_m[-1]  # e.g. 20294
            else:
                shared["auction_no"] = raw_ident

            # Deterministic location extraction from auction_identifier
            # Example: MSTC/SRO/BSNL,TRICHY/13/TRICHY/26-27/20294 -> TRICHY
            parts = [p.strip() for p in raw_ident.split('/') if p.strip()]
            extracted_loc = None
            for i, part in enumerate(parts):
                if re.match(r'^\d{2}-\d{2}$', part) and i > 0:
                    candidate = parts[i - 1]
                    if candidate and not candidate.isdigit():
                        extracted_loc = candidate
                        break

            if not extracted_loc and len(parts) >= 5:
                cand = parts[4]
                if cand and not cand.isdigit():
                    extracted_loc = cand

            if extracted_loc:
                shared["assets_location"] = re.sub(r'\s+', ' ', extracted_loc).strip().upper()

        # 2. Catalogue View Date
        cat_date_m = re.search(r'(?i)(?:Catalogue\s+View\s+Date|View\s+Date|Catalogue\s+Date|Notice\s+Date)\s*[:.-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})', text)
        if cat_date_m:
            dt_s = cat_date_m.group(1).strip().replace(".", "-").replace("/", "-")
            parts = dt_s.split("-")
            if len(parts) == 3 and len(parts[2]) == 2:
                parts[2] = "20" + parts[2]
            shared["catalogue_view_date"] = "-".join(parts)

        # 3. Inspection Schedule (e.g. 15-07-26 to 27-07-26)
        insp_m = re.search(r'(?i)(?:Inspection\s+Schedule|Inspection\s+Period|Inspection\s+Date)\s*[:.-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})\s*(?:to|-)\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})', text)
        if insp_m:
            f_dt = insp_m.group(1).strip().replace(".", "-").replace("/", "-")
            t_dt = insp_m.group(2).strip().replace(".", "-").replace("/", "-")
            f_p = f_dt.split("-")
            t_p = t_dt.split("-")
            if len(f_p) == 3 and len(f_p[2]) == 2:
                f_p[2] = "20" + f_p[2]
            if len(t_p) == 3 and len(t_p[2]) == 2:
                t_p[2] = "20" + t_p[2]
            shared["inspection_schedule_from_date"] = "-".join(f_p) + " 00:00"
            shared["inspection_schedule_to_date"] = "-".join(t_p) + " 00:00"

        # 4. Auction Start Date & Close Date Independent Parsing
        start_label_exists = bool(re.search(r'(?i)Scheduled\s+Auction\s+Start\s+Date', text))
        close_label_exists = bool(re.search(r'(?i)Scheduled\s+Auction\s+Close\s+Date', text))

        start_m = re.search(r'(?i)(?:Scheduled\s+Auction\s+Start\s+Date[\s\n\r]*and\s+Time|Start\s+Date\s+and\s+Time|Auction\s+Start\s+Date)\s*[:.-]?[\s\n\r]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\s+\d{1,2}:\d{2})', text)
        if start_m:
            dt_s = start_m.group(1).strip().replace(".", "-").replace("/", "-")
            d_part, t_part = dt_s.split()[0], dt_s.split()[1]
            p = d_part.split("-")
            if len(p) == 3 and len(p[2]) == 2:
                p[2] = "20" + p[2]
            shared["auction_date_time"] = "-".join(p) + " " + t_part

        close_m = re.search(r'(?i)(?:Scheduled\s+Auction\s+Close\s+Date[\s\n\r]*and\s+Time|Close\s+Date\s+and\s+Time|Auction\s+Close\s+Date|Auction\s+End\s+Date)\s*[:.-]?[\s\n\r]*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\s+\d{1,2}:\d{2})', text)
        if close_m:
            dt_s = close_m.group(1).strip().replace(".", "-").replace("/", "-")
            d_part, t_part = dt_s.split()[0], dt_s.split()[1]
            p = d_part.split("-")
            if len(p) == 3 and len(p[2]) == 2:
                p[2] = "20" + p[2]
            shared["auction_end_date_time"] = "-".join(p) + " " + t_part

        # AUCTION TIMELINE PARSER DEBUG TRACE & VALIDATION
        safe_print("\n=== AUCTION TIMELINE PARSER ===")
        safe_print(f"Start Label Found:\n{'YES' if start_label_exists else 'NO'}\n")
        safe_print(f"Start Value:\n{shared.get('auction_date_time')}\n")
        safe_print(f"Mapped:\nauction_date_time\n")
        safe_print("--------------------------------\n")
        safe_print(f"Close Label Found:\n{'YES' if close_label_exists else 'NO'}\n")
        safe_print(f"Close Value:\n{shared.get('auction_end_date_time')}\n")
        safe_print(f"Mapped:\nauction_end_date_time\n")
        safe_print("--------------------------------\n")

        if start_label_exists and not shared.get("auction_date_time"):
            safe_print("Validation:\nFAIL\n")
            err_msg = "AUCTION TIMELINE PARSER ERROR\nReason: Start date label detected but auction_date_time was not populated."
            logger.error(err_msg)
            raise ValueError(err_msg)

        if shared.get("auction_end_date_time") and not shared.get("auction_date_time") and start_label_exists:
            safe_print("Validation:\nFAIL\n")
            err_msg = "AUCTION TIMELINE PARSER ERROR\nReason: auction_end_date_time exists but auction_date_time is NULL."
            logger.error(err_msg)
            raise ValueError(err_msg)

        safe_print("Validation:\nPASS\n")

        # 6. Pre-Bid EMD Amount (e.g. Pre-Bid EMD Amount: 50000)
        emd_m = re.search(r'(?i)(?:Pre-Bid\s+EMD\s+Amount|EMD\s+Amount|Pre-Bid\s+EMD)\s*[:.-]?\s*(\d+(?:\.\d+)?)', text)
        if emd_m:
            try:
                shared["pre_bid_emd_amount"] = float(emd_m.group(1))
            except Exception:
                pass

        # 7. Auto-extension Time Extraction, Normalization & Validation
        # Required Mapping Labels:
        # - Auction Auto-extension Time
        # - Auction Auto Extension Time
        # - Auto Extension Time
        # - Auto-extension Time
        # - Extension Time
        # - Auction Extend Time
        search_ext_text = text or ""
        ext_label_pattern = r'(?i)(?:Auction\s+Auto[- ]extension\s+Time|Auto[- ]extension\s+Time|Extension\s+Time|Auction\s+Extend\s+Time)'
        val_pattern = r'(?i)(?:Auction\s+Auto[- ]extension\s+Time|Auto[- ]extension\s+Time|Extension\s+Time|Auction\s+Extend\s+Time)\s*[:.-]?[\s\n\r]*([^\n\r]+)'

        if full_pdf_text and not re.search(ext_label_pattern, search_ext_text):
            search_ext_text = full_pdf_text

        ext_label_exists = bool(re.search(ext_label_pattern, search_ext_text))
        ext_m = re.search(val_pattern, search_ext_text)

        raw_ext_val = None
        if ext_m:
            raw_ext_val = ext_m.group(1).strip()
            digits = re.findall(r'\d+', raw_ext_val)
            if digits:
                shared["auction_extend_time"] = int(digits[0])
                shared["auto_extension"] = "Yes"

        # Runtime Debug Logs
        if ext_label_exists:
            safe_print("\n=== AUTO EXTENSION PARSER ===")
            safe_print(f"Label Found:\nYES\n")
            if raw_ext_val:
                safe_print(f"Raw Value:\n{raw_ext_val}\n")
            if shared.get("auction_extend_time") is not None:
                safe_print(f"Normalized:\n{shared.get('auction_extend_time')}\n")
                safe_print(f"Mapped Field:\nauction_extend_time\n")
                safe_print("Status:\nPASS\n")
            else:
                safe_print(f"Mapped Field:\nNULL\n")
                safe_print("Status:\nFAIL\n")

            if shared.get("auction_extend_time") is None:
                err_msg = (
                    "AUTO EXTENSION PARSER ERROR\n\n"
                    "Label Found:\nYES\n\n"
                    "Value Extracted:\nNO\n\n"
                    "Field:\nauction_extend_time"
                )
                logger.error(err_msg)
                raise ValueError(err_msg)

        # 8. Currency
        curr_m = re.search(r'(?i)Currency\s*[:.-]?\s*([A-Z]{3})', text)
        if curr_m:
            shared["currency"] = curr_m.group(1).strip()

        logger.info("Header Metadata Extracted cleanly (Auction Ident: %s, Auction No: %s, Location: %s, View Date: %s, Extend Time: %s).",
                    shared.get("auction_identifier"), shared.get("auction_no"), shared.get("assets_location"), shared.get("catalogue_view_date"), shared.get("auction_extend_time"))

        return shared
