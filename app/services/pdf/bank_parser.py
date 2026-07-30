"""
Bank & Beneficiary Parser for PDF Auction Processing Pipeline.
Extracts seller/EMD payment account details (Beneficiary Name, Bank Name, Branch, Account Number, IFSC).
"""

import re
from app.core.logger import get_logger

logger = get_logger(__name__)


class BankParser:
    """
    Extracts payment bank account details from Seller Account / Beneficiary Details sections.
    """

    def parse_bank(self, text: str, full_pdf_text: str = "") -> dict:
        """
        Extract bank details dict.
        """
        combined = (text or "") + "\n" + (full_pdf_text or "")
        bank_data = {
            "beneficiary_name": None,
            "emd_bank_name": None,
            "branch_name": None,
            "emd_account_number": None,
            "emd_account_no": None,
            "emd_ifsc": None
        }

        if not combined.strip():
            return bank_data

        # 1. Beneficiary Name / Payment Favoring
        ben_m = re.search(r'(?i)(?:Beneficiary\s+Name/Payment\s+favoring|Beneficiary\s+Name|Payment\s+favoring|Account\s+Holder|Favoring)\s*[:.-]?\s*([^\n]+)', combined)
        if ben_m:
            bank_data["beneficiary_name"] = ben_m.group(1).strip()

        # 2. Bank Name
        bname_m = re.search(r'(?i)\bBank\s+Name\s*[:.-]?\s*([^\n]+)', combined)
        if bname_m:
            bank_data["emd_bank_name"] = bname_m.group(1).strip()

        # 3. Branch Name
        branch_m = re.search(r'(?i)\bBranch\s*[:.-]?\s*([^\n]+)', combined)
        if branch_m:
            branch_val = branch_m.group(1).strip()
            # Exclude false positives like "Branch Name :"
            if branch_val.lower() not in ("name", "code", "address"):
                bank_data["branch_name"] = branch_val

        # 4. Account Number (A/c No)
        acc_m = re.search(r'(?i)(?:A/c\s+No|Account\s+No|Account\s+Number|A/C\s+Num)\s*[:.-]?\s*([A-Z0-9]{8,25})', combined)
        if acc_m:
            acc_val = acc_m.group(1).strip()
            bank_data["emd_account_number"] = acc_val
            bank_data["emd_account_no"] = acc_val

        # 5. IFSC Code (Strict Indian IFSC Regex: 4 letters + 0 + 6 alphanumeric)
        ifsc_m = re.search(r'(?i)(?:IFS\s+Code|IFSC\s+Code|IFSC)\s*[:.-]?\s*([A-Z]{4}0[A-Z0-9]{6})', combined)
        if ifsc_m:
            bank_data["emd_ifsc"] = ifsc_m.group(1).strip().upper()

        logger.info("Bank Account Details Extracted (Bank: %s, Branch: %s, Account: %s, IFSC: %s).",
                    bank_data.get("emd_bank_name"), bank_data.get("branch_name"),
                    bank_data.get("emd_account_number"), bank_data.get("emd_ifsc"))

        return bank_data
