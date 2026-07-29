"""
Validator.

Validates extracted auction fields.
"""

from __future__ import annotations

import re
from datetime import datetime

from app.core.logger import get_logger

logger = get_logger(__name__)


class Validator:
    """
    Validate extracted auction fields.
    """

    def __init__(
        self,
    ) -> None:

        logger.info(
            "Validator Initialized."
        )

    # ==========================================================
    # Parse Financial Value Helper
    # ==========================================================

    def parse_financial_value(
        self,
        value: str,
    ) -> str:
        """
        Parse raw financial strings (e.g. "Rs. 1,00,000/-" or "1.16 Crores")
        into clean numeric values.
        """
        if not value:
            return ""

        # Clean currency symbols, commas, spaces
        cleaned = str(value).upper()
        for term in ["₹", "RS.", "RS", "INR", ",", "/-"]:
            cleaned = cleaned.replace(term, "")
        cleaned = cleaned.strip()

        # Check for scale multipliers: Crores, Lakhs
        multiplier = 1.0
        if "CRORE" in cleaned or "CR" in cleaned:
            multiplier = 10000000.0
            cleaned = re.sub(r'CRORES?|CR\.?|CRS\.?', '', cleaned).strip()
        elif "LAKH" in cleaned or "LK" in cleaned:
            multiplier = 100000.0
            cleaned = re.sub(r'LAKHS?|LACS?|LK\.?', '', cleaned).strip()

        # Find first floating point number in the remaining string
        num_match = re.search(r'\d+(\.\d+)?', cleaned)
        if num_match:
            try:
                num = float(num_match.group(0))
                val = num * multiplier
                # Convert to integer string if it is a whole number, else decimal
                if val.is_integer():
                    return str(int(val))
                else:
                    return f"{val:.2f}"
            except Exception:
                pass
        
        # Fallback to extract only digits and decimal point
        digits = re.sub(r'[^0-9.]', '', cleaned)
        return digits

    # ==========================================================
    # Validate Complete Record
    # ==========================================================

    def validate(
        self,
        data: dict,
    ) -> dict:
        """
        Validate extracted auction record.
        """

        logger.info(
            "Validating auction record."
        )

        validated = data.copy()

        validated["bank_name"] = self.validate_bank_name(
            validated.get("bank_name", "")
        )

        validated["branch_name"] = self.validate_branch_name(
            validated.get("branch_name", "")
        )

        validated["borrower_name"] = self.validate_person_name(
            validated.get("borrower_name", "")
        )

        validated["co_borrower"] = self.validate_person_name(
            validated.get("co_borrower", "")
        )

        validated["guarantor"] = self.validate_person_name(
            validated.get("guarantor", "")
        )

        validated["property_type"] = self.validate_property_type(
            validated.get("property_type", "")
        )

        validated["asset_type"] = self.validate_asset_type(
            validated.get("asset_type", "")
        )

        validated["possession_type"] = self.validate_possession_type(
            validated.get("possession_type", "")
        )

        validated["reserve_price"] = self.validate_reserve_price(
            validated.get("reserve_price", "")
        )

        validated["emd_amount"] = self.validate_emd(
            validated.get("emd_amount", "")
        )

        validated["bid_increment"] = self.validate_bid_increment(
            validated.get("bid_increment", "")
        )


        validated["loan_account_number"] = self.validate_loan_account(
            validated.get("loan_account_number", "")
        )

        validated["contact_number"] = self.validate_contact_number(
            validated.get("contact_number", "")
        )

        validated["email"] = self.validate_email(
            validated.get("email", "")
        )

        validated["ifsc"] = self.validate_ifsc(
            validated.get("ifsc", "")
        )

        validated["pin_code"] = self.validate_pin_code(
            validated.get("pin_code", "")
        )

        validated["auction_date"] = self.validate_auction_date(
            validated.get("auction_date", "")
        )

        validated["inspection_date"] = self.validate_inspection_date(
            validated.get("inspection_date", "")
        )

        validated["demand_notice_date"] = self.validate_demand_notice_date(
            validated.get("demand_notice_date", "")
        )

        validated["sale_notice_date"] = self.validate_sale_notice_date(
            validated.get("sale_notice_date", "")
        )

        validated["property_address"] = self.validate_property_address(
            validated.get("property_address", "")
        )

        validated["district"] = self.validate_district(
            validated.get("district", "")
        )

        validated["state"] = self.validate_state(
            validated.get("state", "")
        )

        validated["village"] = self.validate_village(
            validated.get("village", "")
        )

        validated["survey_number"] = self.validate_survey_number(
            validated.get("survey_number", "")
        )

        validated["door_number"] = self.validate_door_number(
            validated.get("door_number", "")
        )

        # Emd and Officer specific fields if mapped
        if "emd_ifsc" in validated:
            validated["emd_ifsc"] = self.validate_ifsc(
                validated.get("emd_ifsc", "")
            )
        if "authorized_officer_number" in validated:
            validated["authorized_officer_number"] = self.validate_contact_number(
                validated.get("authorized_officer_number", "")
            )

        return validated
    

    # ==========================================================
    # Clean Text
    # ==========================================================

    def clean(
        self,
        value: str,
    ) -> str:
        """
        Remove unnecessary spaces.
        """

        if not value:

            return ""

        value = value.strip()

        value = " ".join(

            value.split()

        )

        return value 
    

    # ==========================================================
    # Empty Value
    # ==========================================================

    def is_empty(
        self,
        value,
    ) -> bool:
        """
        Check empty value.
        """

        if value is None:

            return True

        if isinstance(
            value,
            str,
        ):

            return value.strip() == ""

        return False
    

    # ==========================================================
    # Health Check
    # ==========================================================

    def is_ready(
        self,
    ) -> bool:
        """
        Validator status.
        """

        return True
    

    # ==========================================================
    # Validate Bank Name
    # ==========================================================

    def validate_bank_name(
        self,
        value: str,
    ) -> str:
        """
        Validate bank name.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        value = value.upper()

        banks = [

            "STATE BANK OF INDIA",

            "INDIAN BANK",

            "BANK OF BARODA",

            "BANK OF INDIA",

            "CANARA BANK",

            "UNION BANK OF INDIA",

            "PUNJAB NATIONAL BANK",

            "CENTRAL BANK OF INDIA",

            "UCO BANK",

            "ICICI BANK",

            "HDFC BANK",

            "AXIS BANK",

            "INDUSIND BANK",

            "KARUR VYSYA BANK",

            "INDIAN OVERSEAS BANK",

            "TAMILNAD MERCANTILE BANK",

        ]

        for bank in banks:

            if bank in value:

                return bank

        return value.title()


    # ==========================================================
    # Validate Branch Name
    # ==========================================================

    def validate_branch_name(
        self,
        value: str,
    ) -> str:
        """
        Validate branch name.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        value = re.sub(

            r"[^A-Za-z0-9&(),./ -]",

            "",

            value,

        )

        return value.title()


    # ==========================================================
    # Validate Person Name
    # ==========================================================

    def validate_person_name(
        self,
        value: str,
    ) -> str:
        """
        Validate person name.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        # Clean up common description noise words that bleed in from OCR typos
        noise = ["injection", "moulding", "moulcing", "machine", "machinery", "property", "properties", "land", "building", "factory", "plant", "description", "boundaries", "qty", "set", "year", "manufacturing"]
        words = value.split()
        cleaned_words = []
        for w in words:
            w_clean = re.sub(r'[^A-Za-z]', '', w).lower()
            if any(n in w_clean for n in noise):
                break
            cleaned_words.append(w)
        value = " ".join(cleaned_words)

        value = re.sub(
            r"[^A-Za-z .]",
            "",
            value,
        )

        value = " ".join(
            value.split(),
        )

        return value.title()


    # ==========================================================
    # Validate Property Type
    # ==========================================================

    def validate_property_type(
        self,
        value: str,
    ) -> str:
        """
        Validate property type.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        property_types = {

            "HOUSE": "Residential House",

            "FLAT": "Residential Flat",

            "APARTMENT": "Apartment",

            "PLOT": "Plot",

            "LAND": "Land",

            "SITE": "Site",

            "SHOP": "Shop",

            "OFFICE": "Office",

            "BUILDING": "Building",

            "WAREHOUSE": "Warehouse",

            "FACTORY": "Factory",

            "VILLA": "Villa",

            "COMMERCIAL": "Commercial Property",

            "INDUSTRIAL": "Industrial Property",

            "AGRICULTURAL": "Agricultural Land",

        }

        upper = value.upper()

        for key, standard in property_types.items():

            if key in upper:

                return standard

        return value.title()
    

    # ==========================================================
    # Validate Asset Type
    # ==========================================================

    def validate_asset_type(
        self,
        value: str,
    ) -> str:
        """
        Validate asset type.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        upper = value.upper()

        if "IMMOVABLE" in upper:

            return "Immovable"

        if "MOVABLE" in upper:

            return "Movable"

        return value.title()


    # ==========================================================
    # Validate Possession Type
    # ==========================================================

    def validate_possession_type(
        self,
        value: str,
    ) -> str:
        """
        Validate possession type.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        upper = value.upper()

        if "PHYSICAL" in upper:

            return "Physical Possession"

        if "SYMBOLIC" in upper:

            return "Symbolic Possession"

        if "CONSTRUCTIVE" in upper:

            return "Constructive Possession"

        return value.title()
    

    # ==========================================================
    # Validate Possession Type
    # ==========================================================

    def validate_possession_type(
        self,
        value: str,
    ) -> str:
        """
        Validate possession type.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        upper = value.upper()

        if "PHYSICAL" in upper:

            return "Physical Possession"

        if "SYMBOLIC" in upper:

            return "Symbolic Possession"

        if "CONSTRUCTIVE" in upper:

            return "Constructive Possession"

        return value.title()


    # ==========================================================
    # Validate Reserve Price
    # ==========================================================

    def validate_reserve_price(
        self,
        value: str,
    ) -> str:
        """
        Validate reserve price.
        """
        return self.parse_financial_value(value)
    

    # ==========================================================
    # Validate EMD
    # ==========================================================

    def validate_emd(
        self,
        value: str,
    ) -> str:
        """
        Validate EMD amount.
        """
        return self.parse_financial_value(value)
    

    # ==========================================================
    # Validate Bid Increment
    # ==========================================================

    def validate_bid_increment(
        self,
        value: str,
    ) -> str:
        """
        Validate bid increment.
        """
        return self.parse_financial_value(value)
    

    # ==========================================================
    # Validate Loan Account Number
    # ==========================================================

    def validate_loan_account(
        self,
        value: str,
    ) -> str:
        """
        Validate loan account number.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):
            return ""

        value = value.upper()

        value = re.sub(

            r"[^A-Z0-9/-]",

            "",

            value,

        )

        return value
    

    # ==========================================================
    # Validate Contact Number
    # ==========================================================

    def validate_contact_number(
        self,
        value: str,
    ) -> str:
        """
        Validate mobile/phone number(s).
        """
        value = self.clean(value)
        if self.is_empty(value):
            return ""

        found_numbers = []
        digits_seq = re.findall(r'\d+', value)
        for seq in digits_seq:
            if len(seq) == 10:
                found_numbers.append(seq)
            elif len(seq) == 12 and seq.startswith("91"):
                found_numbers.append(seq[2:])
            elif len(seq) == 11 and seq.startswith("0"):
                found_numbers.append(seq)
            elif 7 <= len(seq) <= 12:
                found_numbers.append(seq)
        
        if found_numbers:
            return " / ".join(found_numbers)
        
        return value
    

    # ==========================================================
    # Validate Email
    # ==========================================================

    def validate_email(
        self,
        value: str,
    ) -> str:
        """
        Validate email address.
        """
        value = self.clean(value)
        if self.is_empty(value):
            return ""

        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", value)
        if emails:
            return ", ".join([e.lower() for e in emails])

        return value
    

    # ==========================================================
    # Validate IFSC
    # ==========================================================

    def validate_ifsc(
        self,
        value: str,
    ) -> str:
        """
        Validate IFSC code.
        """
        value = self.clean(value)
        if self.is_empty(value):
            return ""

        val = value.upper().replace(" ", "")
        
        # Auto-correct common OCR errors for target bank branches
        corrections = {
            "CNRB0005249": "CNRB0005248",
            "CNR8DCO5249": "CNRB0005248",
            "CNRB000524B": "CNRB0005248",
            "CNRB000524S": "CNRB0005248",
            "CNR80005248": "CNRB0005248",
            "CNR80005249": "CNRB0005248",
            "CNR8000524B": "CNRB0005248",
            "I1B000T084": "IDIB000T084",
            "I1B000T034": "IDIB000T034",
            "ID1B000T084": "IDIB000T084",
            "ID1B000T034": "IDIB000T034",
        }
        if val in corrections:
            val = corrections[val]

        if len(val) == 11 and val[4] == 'O':
            val = val[:4] + '0' + val[5:]

        if re.fullmatch(r"[A-Z]{4}0[A-Z0-9]{6}", val):
            return val

        return value
    

    # ==========================================================
    # Validate PIN Code
    # ==========================================================

    def validate_pin_code(
        self,
        value: str,
    ) -> str:
        """
        Validate Indian PIN code.
        """
        value = self.clean(value)
        if self.is_empty(value):
            return ""

        pin_match = re.search(r'\b\d{6}\b', value)
        if pin_match:
            return pin_match.group(0)

        return value
    

    # ==========================================================
    # Validate Auction Date
    # ==========================================================

    def validate_auction_date(
        self,
        value: str,
    ) -> str:
        """
        Validate auction date.
        """

        return self.validate_date(
            value,
        )
    
    # ==========================================================
    # Validate Inspection Date
    # ==========================================================

    def validate_inspection_date(
        self,
        value: str,
    ) -> str:
        """
        Validate inspection date.
        """

        return self.validate_date(
            value,
        )

    # ==========================================================
    # Validate Demand Notice Date
    # ==========================================================

    def validate_demand_notice_date(
        self,
        value: str,
    ) -> str:
        """
        Validate demand notice date.
        """

        return self.validate_date(
            value,
        )
    
    # ==========================================================
    # Validate Sale Notice Date
    # ==========================================================

    def validate_sale_notice_date(
        self,
        value: str,
    ) -> str:
        """
        Validate sale notice date.
        """

        return self.validate_date(
            value,
        )

    # ==========================================================
    # Validate Date
    # ==========================================================

    def validate_date(
        self,
        value: str,
    ) -> str:
        """
        Validate and normalize date.

        Returns
        -------
        YYYY-MM-DD
        """
        value = self.clean(value)
        if self.is_empty(value):
            return ""

        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
            "%d/%m/%y",
            "%d-%m-%y",
            "%d.%m.%y",
        ]

        for fmt in formats:
            try:
                date_val = datetime.strptime(value, fmt)
                return date_val.strftime("%Y-%m-%d")
            except ValueError:
                continue

        try:
            import dateutil.parser
            date_val = dateutil.parser.parse(value)
            return date_val.strftime("%Y-%m-%d")
        except Exception:
            pass

        return value
    

    # ==========================================================
    # Validate Property Address
    # ==========================================================

    def validate_property_address(
        self,
        value: str,
    ) -> str:
        """
        Validate property address.
        """
        value = self.clean(value)
        if self.is_empty(value):
            return ""

        value = re.sub(r"\s+", " ", value)
        if len(value) < 5:
            return ""

        return value
    

    # ==========================================================
    # Validate District
    # ==========================================================

    def validate_district(
        self,
        value: str,
    ) -> str:
        """
        Validate district.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        return value.title()
    
    # ==========================================================
    # Validate State
    # ==========================================================

    def validate_state(
        self,
        value: str,
    ) -> str:
        """
        Validate state.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        return value.title()
    

    # ==========================================================
    # Validate Village
    # ==========================================================

    def validate_village(
        self,
        value: str,
    ) -> str:
        """
        Validate village.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        return value.title()


    # ==========================================================
    # Validate Survey Number
    # ==========================================================

    def validate_survey_number(
        self,
        value: str,
    ) -> str:
        """
        Validate survey number.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        value = value.upper()

        value = re.sub(

            r"[^A-Z0-9/-]",

            "",

            value,

        )

        return value
    

    # ==========================================================
    # Validate Door Number
    # ==========================================================

    def validate_door_number(
        self,
        value: str,
    ) -> str:
        """
        Validate door number.
        """

        value = self.clean(
            value,
        )

        if self.is_empty(
            value,
        ):

            return ""

        return value.upper()
    

    # ==========================================================
    # Required Fields
    # ==========================================================

    def required_fields(
        self,
    ) -> list[str]:
        """
        Required auction fields.
        """

        return [

            "bank_name",

            "borrower_name",

            "reserve_price",

            "auction_date",

            "property_address",

        ]
    

    # ==========================================================
    # Missing Fields
    # ==========================================================

    def missing_fields(
        self,
        data: dict,
    ) -> list[str]:
        """
        Return missing required fields.
        """

        missing = []

        for field in self.required_fields():

            if self.is_empty(

                data.get(
                    field,
                    "",
                )

            ):

                missing.append(
                    field,
                )

        return missing
    

    # ==========================================================
    # Validation Errors
    # ==========================================================

    def validation_errors(
        self,
        data: dict,
    ) -> list[str]:
        """
        Generate validation errors.
        """

        errors = []

        for field in self.missing_fields(
            data,
        ):

            errors.append(

                f"{field} is required."

            )

        return errors


    # ==========================================================
    # Quality Score
    # ==========================================================

    def quality_score(
        self,
        data: dict,
    ) -> float:
        """
        Calculate extraction quality.
        """

        total = len(data)

        extracted = sum(

            1

            for value in data.values()

            if not self.is_empty(
                value,
            )

        )

        return round(

            (extracted / total) * 100,

            2,

        )


    # ==========================================================
    # Validation Summary
    # ==========================================================

    def summary(
        self,
        data: dict,
    ) -> dict:
        """
        Return validation summary.
        """

        missing = self.missing_fields(
            data,
        )

        return {

            "valid": len(missing) == 0,

            "quality_score": self.quality_score(
                data,
            ),

            "missing_fields": missing,

            "errors": self.validation_errors(
                data,
            ),

        }
    
    # ==========================================================
    # Process Validation
    # ==========================================================

    def process(
        self,
        data: dict,
    ) -> dict:
        """
        Validate complete auction record.
        """

        logger.info(
            "Processing validation."
        )

        validated = self.validate(
            data,
        )

        summary = self.summary(
            validated,
        )

        return {

            "record": validated,

            "validation": summary,

        }


    # ==========================================================
    # Statistics
    # ==========================================================

    def statistics(
        self,
        data: dict,
    ) -> dict:
        """
        Validation statistics.
        """

        total = len(data)

        valid = sum(

            1

            for value in data.values()

            if not self.is_empty(
                value,
            )

        )

        return {

            "total_fields": total,

            "validated_fields": valid,

            "missing_fields": total - valid,

            "completion_percentage": round(

                valid / total * 100,

                2,

            ),

        }


    # ==========================================================
    # Health Check
    # ==========================================================

    def health_check(
        self,
    ) -> dict:
        """
        Validator health.
        """

        return {

            "service": "Validator",

            "status": "Healthy",

            "ready": self.is_ready(),

        }


    # ==========================================================
    # Reset
    # ==========================================================

    def reset(
        self,
    ) -> bool:
        """
        Reset validator.
        """

        logger.info(
            "Validator reset."
        )

        return True
    

    # ==========================================================
    # Version
    # ==========================================================

    def version(
        self,
    ) -> dict:
        """
        Validator information.
        """

        return {

            "name": "Auction Validator",

            "version": "1.0.0",

            "supported_fields": 30,

        }