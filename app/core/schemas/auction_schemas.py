"""
Auction Schemas and response formatting.
"""

from datetime import date, datetime
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

def safe_print(msg: str):
    try:
        print(msg)
    except Exception:
        pass

SCRAP_FIELDS = [
    "asset_type", "asset_category", "auction_no", "auction_description", "auction_type",
    "assets_location", "starting_price", "reserve_price", "pre_bid_emd", "emd_price", "increment_price", "currency",
    "auction_date_time", "auction_end_date_time", "auto_extension", "auto_extension_mode",
    "auction_extend_time", "auction_live_status", "first_bid_acceptance_condition",
    "inspection_schedule_from_date", "inspection_schedule_to_date", "submit_application",
    "emd_bank_name", "emd_account_number", "emd_ifsc", "auction_office", "institution_seller",
    "auction_department", "digital_certificate", "catalogue_view_date", "asset_subcategory",
    "full_payment_balance", "delivery_of_material_taken", "quantity", "units",
    "start_floor_price", "remarks", "authorized_officer_name", "authorized_officer_number",
    "vendor_name", "payment_type"
]

GOLD_FIELDS = [
    "asset_type", "asset_category", "auction_no", "auction_description", "assets_location",
    "starting_price", "reserve_price", "pre_bid_emd", "emd_price", "increment_price", "currency", "auction_date_time",
    "auction_end_date_time", "auto_extension", "auto_extension_mode", "auction_extend_time",
    "auction_live_status", "first_bid_acceptance_condition", "inspection_schedule_from_date",
    "inspection_schedule_to_date", "submit_application", "emd_bank_name", "emd_account_number",
    "emd_ifsc", "borrower", "asset_subcategory", "institution_seller", "sum_of_carat_18",
    "sum_of_carat_19", "sum_of_carat_20", "sum_of_carat_21", "sum_of_carat_22", "sum_of_carat_23",
    "sum_of_carat_24", "sum_of_net_weight_total", "sum_of_gross_weight_total", "catalogue_view_date",
    "quantity", "units", "start_floor_price", "remarks", "authorized_officer_name",
    "authorized_officer_number", "vendor_name", "payment_type"
]

VEHICLE_FIELDS = [
    "asset_type", "asset_category", "auction_no", "auction_description", "auction_type",
    "assets_location", "starting_price", "reserve_price", "pre_bid_emd", "emd_price", "increment_price", "currency",
    "auction_date_time", "auction_end_date_time", "auto_extension", "auto_extension_mode",
    "auction_extend_time", "auction_live_status", "inspection_schedule_from_date",
    "inspection_schedule_to_date", "submit_application", "emd_bank_name", "emd_account_number",
    "emd_ifsc", "borrower", "institution_seller", "asset_subcategory", "year",
    "registration_number", "repo_date", "km_driven", "rc_number", "chassis_number",
    "yard_rent_percent", "full_payment_balance", "remarks", "authorized_officer_name",
    "authorized_officer_number", "vendor_name", "payment_type"
]

PEARL_FIELDS = [
    "asset_type", "asset_category", "auction_no", "auction_description", "auction_type",
    "assets_location", "starting_price", "reserve_price", "pre_bid_emd", "emd_price", "increment_price", "currency",
    "auction_date_time", "auction_end_date_time", "auto_extension", "auto_extension_mode",
    "auction_extend_time", "auction_live_status", "first_bid_acceptance_condition",
    "inspection_schedule_from_date", "inspection_schedule_to_date", "submit_application",
    "emd_bank_name", "emd_account_number", "emd_ifsc", "remarks", "authorized_officer_name",
    "authorized_officer_number", "vendor_name", "payment_type"
]

PROPERTY_FIELDS = [
    "asset_type", "asset_category", "auction_no", "auction_description", "auction_type",
    "assets_location", "starting_price", "reserve_price", "pre_bid_emd", "emd_price", "increment_price", "currency",
    "auction_date_time", "auction_end_date_time", "auto_extension", "auto_extension_mode",
    "auction_extend_time", "auction_live_status", "first_bid_acceptance_condition",
    "inspection_schedule_from_date", "inspection_schedule_to_date", "submit_application",
    "emd_bank_name", "emd_account_number", "emd_ifsc", "borrower", "institution_seller",
    "auction_office", "auction_department", "event_type", "digital_certificate",
    "catalogue_view_date", "remarks", "authorized_officer_name", "authorized_officer_number",
    "vendor_name", "payment_type"
]


def format_date_to_dmy(val, include_time=False):
    if val in (None, ""):
        return None
    try:
        if isinstance(val, (datetime, date)):
            dt = val
        else:
            dt = dateutil.parser.parse(str(val))
        if include_time:
            return dt.strftime("%d-%m-%Y %H:%M")
        else:
            return dt.strftime("%d-%m-%Y")
    except Exception:
        return None


def clean_numeric(val):
    if val in (None, ""):
        return None
    try:
        f_val = float(val)
        return f_val
    except Exception:
        return None


def build_pipeline_response(result: dict) -> dict:
    """
    Build API response dynamically selecting schemas.
    """
    records_dict = []
    raw_results = result.get("extraction_results", [])
    flat_raw_extracts = []
    visited = set()
    def extract_dicts(obj):
        if id(obj) in visited:
            return
        visited.add(id(obj))
        if isinstance(obj, dict):
            flat_raw_extracts.append(obj)
            for v in obj.values():
                extract_dicts(v)
        elif isinstance(obj, list):
            for item in obj:
                extract_dicts(item)

    for res in raw_results:
        extract_dicts(res)
    extract_dicts(result)

    for idx, record in enumerate(result.get("results", [])):
        if hasattr(record, "__table__"):
            db_dict = {c.key: getattr(record, c.key) for c in record.__table__.columns}
            
            raw_extract = None
            if flat_raw_extracts:
                if idx < len(flat_raw_extracts):
                    raw_extract = flat_raw_extracts[idx]
                else:
                    raw_extract = flat_raw_extracts[0]
            
            category = str(db_dict.get("asset_category") or "").lower()
            asset_type_val = str(db_dict.get("asset_type") or "").lower()
            
            # Standardize asset_type
            if "immovable" in asset_type_val or category in ("property", "residential", "commercial", "industrial", "land", "flat", "house", "building", "plot", "real estate"):
                asset_type_normalized = "Immovable"
            elif "movable" in asset_type_val:
                asset_type_normalized = "Movable"
            else:
                asset_type_normalized = None

            # Select category schema (Property / Immovable defaults to PROPERTY_SCHEMA)
            if category == "scrap":
                schema_fields = SCRAP_FIELDS
                schema_name = "SCRAP_SCHEMA"
            elif category == "gold":
                schema_fields = GOLD_FIELDS
                schema_name = "GOLD_SCHEMA"
            elif category == "vehicle":
                schema_fields = VEHICLE_FIELDS
                schema_name = "VEHICLE_SCHEMA"
            elif category == "pearl":
                schema_fields = PEARL_FIELDS
                schema_name = "PEARL_SCHEMA"
            elif category in ("property", "residential", "commercial", "industrial", "land", "flat", "house", "building", "plot", "real estate") or asset_type_normalized == "Immovable":
                schema_fields = PROPERTY_FIELDS
                schema_name = "PROPERTY_SCHEMA"
            else:
                # Default Movable assets to SCRAP_SCHEMA (Movable category) instead of PROPERTY_SCHEMA
                schema_fields = SCRAP_FIELDS
                schema_name = "SCRAP_SCHEMA"

            # Step 4: Log category schema selection
            import sys
            def safe_print_local(text: str):
                try:
                    sys.stdout.write(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace") + "\n")
                except Exception:
                    pass
            safe_print_local("\n=== STEP 4: CATEGORY SCHEMA SELECTION ===")
            safe_print_local(f"  Detected Asset Type    : {asset_type_normalized}")
            safe_print_local(f"  Detected Asset Category: {category.upper()}")
            safe_print_local(f"  Schema Selected        : {schema_name}")
            safe_print_local("=========================================\n")

            # Build clean records mapping dict
            record_dict = {field: None for field in schema_fields}

            record_dict["asset_type"] = asset_type_normalized
            record_dict["asset_category"] = category or None

            # Sanitize auction_no: Never allow Seller Name to populate auction_no
            raw_auc_no = str(db_dict.get("auction_no") or "").strip()
            seller_str = str(db_dict.get("institution_seller") or "").strip()
            if raw_auc_no and (len(raw_auc_no) > 15 or (seller_str and raw_auc_no.lower() in seller_str.lower())):
                record_dict["auction_no"] = str(db_dict.get("lot_no") or "1")
            else:
                record_dict["auction_no"] = raw_auc_no or str(db_dict.get("lot_no") or "") or None

            record_dict["auction_description"] = db_dict.get("auction_description") or None
            raw_loc = None
            if raw_extract and isinstance(raw_extract, dict):
                raw_loc = raw_extract.get("assets_location") or raw_extract.get("property_address") or raw_extract.get("address") or raw_extract.get("location")
            if not raw_loc and flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        found_loc = item.get("assets_location") or item.get("property_address") or item.get("address") or item.get("location")
                        if found_loc:
                            raw_loc = found_loc
                            break
            record_dict["assets_location"] = db_dict.get("assets_location") or db_dict.get("property_address") or raw_loc or None

            # Notice bank details and branch office department mapping
            bank_val = db_dict.get("institution_seller") or None
            if "institution_seller" in record_dict:
                record_dict["institution_seller"] = bank_val
            
            if "auction_office" in record_dict:
                record_dict["auction_office"] = db_dict.get("auction_office") or db_dict.get("auction_office_department") or db_dict.get("branch_name") or None
            if "auction_department" in record_dict:
                record_dict["auction_department"] = db_dict.get("auction_department") or db_dict.get("auction_office_department") or None

            # Borrower mapping
            bor_val = db_dict.get("borrower") or db_dict.get("borrower_name") or None
            if "borrower" in record_dict:
                record_dict["borrower"] = bor_val

            # EMD details mapping with dynamic fallback scanning (Rule 1)
            emd_bank = db_dict.get("emd_bank_name")
            emd_acc = db_dict.get("emd_account_no") or db_dict.get("emd_account_number")
            emd_ifsc_val = db_dict.get("emd_ifsc") or db_dict.get("ifsc")

            if flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        if not emd_bank:
                            emd_bank = item.get("emd_bank_name") or item.get("beneficiary_bank")
                        if not emd_acc:
                            emd_acc = item.get("emd_account_no") or item.get("emd_account_number") or item.get("account_number")
                        if not emd_ifsc_val:
                            emd_ifsc_val = item.get("emd_ifsc") or item.get("ifsc")

            # Priority 2 - Default to institution_seller if seller is a bank and no separate payment bank is found
            if not emd_bank and bank_val:
                seller_s = str(bank_val).strip()
                if "bank" in seller_s.lower():
                    emd_bank = seller_s

            if "emd_bank_name" in record_dict:
                record_dict["emd_bank_name"] = emd_bank or None
            if "emd_account_number" in record_dict:
                record_dict["emd_account_number"] = emd_acc or None
            if "emd_ifsc" in record_dict:
                record_dict["emd_ifsc"] = emd_ifsc_val or None

            # Numeric price conversions (do not default missing values to 0)
            reserve_val = clean_numeric(db_dict.get("reserve_price") or db_dict.get("starting_price") or db_dict.get("auction_start_price"))
            record_dict["starting_price"] = reserve_val
            record_dict["reserve_price"] = reserve_val

            emd_val = clean_numeric(db_dict.get("emd_price") or db_dict.get("emd_amount") or db_dict.get("pre_bid_emd"))
            record_dict["pre_bid_emd"] = emd_val
            record_dict["emd_price"] = emd_val

            inc_val = clean_numeric(db_dict.get("increment_price") or db_dict.get("bid_increment"))
            record_dict["increment_price"] = inc_val

            record_dict["currency"] = db_dict.get("currency") or "INR"

            # Dropdowns Normalized Values or null (None)
            # 1. Auction Type
            auc_type = str(db_dict.get("auction_type") or "").lower()
            if "forward" in auc_type or "1" in auc_type:
                record_dict["auction_type"] = "Forward"
            elif "reverse" in auc_type or "2" in auc_type:
                record_dict["auction_type"] = "Reverse"
            elif "tender" in auc_type or "3" in auc_type:
                record_dict["auction_type"] = "Tender"
            else:
                record_dict["auction_type"] = None

            # 2. Auto Extension
            auto_ext = db_dict.get("auto_extension")
            raw_ae = None
            if raw_extract:
                raw_ae = raw_extract.get("auto_extension")
            
            if auto_ext is True or str(auto_ext).lower() in ("yes", "true", "1") or str(raw_ae).lower() in ("yes", "true", "1"):
                record_dict["auto_extension"] = "Yes"
            elif raw_ae in (None, ""):
                record_dict["auto_extension"] = None
            else:
                record_dict["auto_extension"] = "No"

            # 3. Auto Extension Mode
            ext_mode = str(db_dict.get("auto_extension_mode") or "").lower()
            if "infinite" in ext_mode or "1" in ext_mode:
                record_dict["auto_extension_mode"] = "Infinite"
            elif "custom" in ext_mode or "2" in ext_mode:
                record_dict["auto_extension_mode"] = "Custom"
            else:
                record_dict["auto_extension_mode"] = None

            # 4. Auction Live Status
            live_status = str(db_dict.get("auction_live_status") or "").lower()
            if "live" in live_status:
                record_dict["auction_live_status"] = "Live"
            elif "reschedule" in live_status:
                record_dict["auction_live_status"] = "Reschedule"
            elif "not active" in live_status or "not_active" in live_status or "notactive" in live_status:
                record_dict["auction_live_status"] = "Not Active"
            elif "cancel" in live_status:
                record_dict["auction_live_status"] = "Cancel"
            else:
                record_dict["auction_live_status"] = None

            # 5. First Bid Acceptance Condition
            first_bid = db_dict.get("first_bid_acceptance_condition")
            if str(first_bid).lower() in ("yes", "true", "1"):
                record_dict["first_bid_acceptance_condition"] = "Yes"
            elif str(first_bid).lower() in ("no", "false", "0"):
                record_dict["first_bid_acceptance_condition"] = "No"
            else:
                record_dict["first_bid_acceptance_condition"] = None

            # 6. Digital Certificate
            digi_cert = db_dict.get("digital_certificate")
            if str(digi_cert).lower() in ("yes", "true", "1"):
                record_dict["digital_certificate"] = "Yes"
            elif str(digi_cert).lower() in ("no", "false", "0"):
                record_dict["digital_certificate"] = "No"
            else:
                record_dict["digital_certificate"] = None

            # 7. Asset SubCategory
            sub_cat = str(db_dict.get("asset_subcategory") or "").lower()
            if category == "scrap":
                if "compressor" in sub_cat:
                    record_dict["asset_subcategory"] = "Compressors"
                elif "e-waste" in sub_cat or "ewaste" in sub_cat:
                    record_dict["asset_subcategory"] = "E-Waste"
                elif "machiner" in sub_cat:
                    record_dict["asset_subcategory"] = "Used and Unused Machineries"
                elif "wood" in sub_cat:
                    record_dict["asset_subcategory"] = "Wood Scrap"
                elif "car" in sub_cat:
                    record_dict["asset_subcategory"] = "Car"
                elif "lki" in sub_cat:
                    record_dict["asset_subcategory"] = "LKI"
                else:
                    record_dict["asset_subcategory"] = None
            elif category == "vehicle":
                record_dict["asset_subcategory"] = "Car"
            else:
                record_dict["asset_subcategory"] = None

            # 8. Vendor name
            vendor = str(db_dict.get("vendor_name") or "").upper()
            valid_vendors = ["ABI", "AS", "TESTEMP", "BINUKUMAR", "FSTEMP", "TEST EMPS", "TEST EMP"]
            found_vendor = False
            for v_opt in valid_vendors:
                if v_opt == vendor or v_opt.replace(" ", "") == vendor.replace(" ", ""):
                    record_dict["vendor_name"] = v_opt
                    found_vendor = True
                    break
            if not found_vendor:
                record_dict["vendor_name"] = None

            # 9. Event Type (Property Event Type Dropdown)
            evt_type = db_dict.get("event_type")
            if evt_type:
                valid_events = ["Insurance Salvage", "REPO", "Sarfaesi", "DRT", "NCLT", "Consumer/Seller", "SARFAESI ACT", "kjno", "binnukutty", "qwerty", "bbbb"]
                evt_upper = str(evt_type).strip().upper()
                found_event = None
                for e_opt in valid_events:
                    if e_opt.upper() == evt_upper:
                        found_event = e_opt
                        break
                record_dict["event_type"] = found_event
            else:
                record_dict["event_type"] = None

            # 10. Payment Type
            payment = db_dict.get("payment_type")
            if payment:
                if category == "property":
                    pay_lower = str(payment).lower()
                    if "amount" in pay_lower:
                        record_dict["payment_type"] = "Amount"
                    elif "transaction" in pay_lower or "value" in pay_lower:
                        record_dict["payment_type"] = "Transaction Value"
                    else:
                        record_dict["payment_type"] = None
                else:
                    record_dict["payment_type"] = payment
            else:
                record_dict["payment_type"] = None

            raw_notice_date = None
            if raw_extract and isinstance(raw_extract, dict):
                for k in ["catalogue_view_date", "notice_date", "publication_date", "issue_date", "issued_date", "date", "place_and_date"]:
                    v = raw_extract.get(k)
                    if v and str(v).strip() not in ("", "None", "null"):
                        raw_notice_date = str(v).strip()
                        break
            
            if not raw_notice_date and flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        for k in ["catalogue_view_date", "notice_date", "publication_date", "issue_date", "issued_date", "date", "place_and_date"]:
                            v = item.get(k)
                            if v and str(v).strip() not in ("", "None", "null"):
                                raw_notice_date = str(v).strip()
                                break
                        if raw_notice_date:
                            break

            cat_raw_val = db_dict.get("catalogue_view_date") or db_dict.get("sale_notice_date") or raw_notice_date
            cat_view = format_date_to_dmy(cat_raw_val) if cat_raw_val else None

            # Inspection dates:
            raw_insp_val = None
            if raw_extract and isinstance(raw_extract, dict):
                raw_insp_val = raw_extract.get("inspection_schedule_from") or raw_extract.get("inspection_schedule_from_date") or raw_extract.get("inspection_from_date")
            
            if not raw_insp_val and flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        found_insp = item.get("inspection_schedule_from") or item.get("inspection_schedule_from_date") or item.get("inspection_from_date")
                        if found_insp and str(found_insp).strip() not in ("", "None", "null"):
                            raw_insp_val = found_insp
                            break

            insp_from = format_date_to_dmy(raw_insp_val, include_time=True) if raw_insp_val else None
            insp_to = format_date_to_dmy(db_dict.get("inspection_to_date"), include_time=True) if raw_insp_val else None

            record_dict["inspection_schedule_from_date"] = insp_from
            record_dict["inspection_schedule_to_date"] = insp_to
            record_dict["catalogue_view_date"] = cat_view

            record_dict["auction_date_time"] = format_date_to_dmy(db_dict.get("auction_start_datetime"), include_time=True)
            record_dict["auction_end_date_time"] = format_date_to_dmy(db_dict.get("auction_end_datetime"), include_time=True)
            record_dict["submit_application"] = format_date_to_dmy(db_dict.get("submit_application"), include_time=True)
            record_dict["repo_date"] = format_date_to_dmy(db_dict.get("repo_date"))

            # Scrap field mappings
            if "delivery_of_material_taken" in record_dict:
                record_dict["delivery_of_material_taken"] = db_dict.get("delivery_of_material_taken") or None
            if "quantity" in record_dict:
                record_dict["quantity"] = db_dict.get("quantity") or None
            if "units" in record_dict:
                record_dict["units"] = db_dict.get("units") or None

            # Gold fields
            for carat in [18, 19, 20, 21, 22, 23, 24]:
                key = f"sum_of_carat_{carat}"
                if key in record_dict:
                    val = db_dict.get(key)
                    record_dict[key] = val if val not in (None, "") else "-"
            if "sum_of_net_weight_total" in record_dict:
                record_dict["sum_of_net_weight_total"] = db_dict.get("sum_of_net_weight_total") or None
            if "sum_of_gross_weight_total" in record_dict:
                record_dict["sum_of_gross_weight_total"] = db_dict.get("sum_of_gross_weight_total") or None

            # Vehicle fields
            if "year" in record_dict:
                record_dict["year"] = db_dict.get("year") or None
            if "registration_number" in record_dict:
                record_dict["registration_number"] = db_dict.get("reg_no") or None
            if "km_driven" in record_dict:
                record_dict["km_driven"] = db_dict.get("km_driven") or None
            if "rc_number" in record_dict:
                record_dict["rc_number"] = db_dict.get("rc") or None
            if "chassis_number" in record_dict:
                record_dict["chassis_number"] = db_dict.get("chassis_number") or None
            if "yard_rent_percent" in record_dict:
                record_dict["yard_rent_percent"] = db_dict.get("yard_rent_percent") or None
            if "full_payment_balance" in record_dict:
                fp_balance = clean_numeric(db_dict.get("full_payment_balance"))
                raw_fp = None
                if raw_extract:
                    raw_fp = raw_extract.get("full_payment_balance") or raw_extract.get("payment_balance")
                if raw_fp in (None, ""):
                    record_dict["full_payment_balance"] = None
                else:
                    record_dict["full_payment_balance"] = fp_balance

            # Auction Extend Time mins vs integer
            if "auction_extend_time" in record_dict:
                ext_time = db_dict.get("auction_extend_time")
                raw_ext_val = None
                if raw_extract:
                    raw_ext_val = raw_extract.get("auction_extend_time") if raw_extract.get("auction_extend_time") is not None else raw_extract.get("auction_extend_time_mins")
                if raw_ext_val in (None, "") and ext_time in (None, ""):
                    record_dict["auction_extend_time"] = None
                else:
                    val_to_use = ext_time if ext_time is not None else raw_ext_val
                    if isinstance(val_to_use, (int, float)):
                        record_dict["auction_extend_time"] = int(val_to_use)
                    elif isinstance(val_to_use, str):
                        digits = re.findall(r'\d+', val_to_use)
                        record_dict["auction_extend_time"] = int(digits[0]) if digits else None
                    else:
                        record_dict["auction_extend_time"] = None

            # Remarks
            if "remarks" in record_dict:
                record_dict["remarks"] = db_dict.get("remarks") or None
            if "authorized_officer_name" in record_dict:
                record_dict["authorized_officer_name"] = db_dict.get("authorized_officer_name") or db_dict.get("authorized_officer") or None
            if "authorized_officer_number" in record_dict:
                record_dict["authorized_officer_number"] = db_dict.get("authorized_officer_number") or db_dict.get("contact_number") or None

            # Dynamic Date Post-Processing Guard: Trace and validate dates strictly against business sources (Rules 1-6)
            cat_view_source = None
            insp_from_source = None
            insp_to_source = None
            auc_date_source = "Auction Timeline"

            # 1. Resolve catalogue_view_date from explicit Notice Metadata (Rules 2 & 3)
            raw_notice_date = None
            notice_source_tag = None

            # Priority 1: Explicit Catalogue View Date
            if raw_extract and isinstance(raw_extract, dict):
                v_cat = raw_extract.get("catalogue_view_date")
                if v_cat and str(v_cat).strip() not in ("", "None", "null"):
                    raw_notice_date = str(v_cat).strip()
                    notice_source_tag = "Catalogue View Date"

            if not raw_notice_date and flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        v_cat = item.get("catalogue_view_date")
                        if v_cat and str(v_cat).strip() not in ("", "None", "null"):
                            raw_notice_date = str(v_cat).strip()
                            notice_source_tag = "Catalogue View Date"
                            break

            # Priority 2 & 3: DATE / Date / DATED / Footer Date / Place + Date
            if not raw_notice_date:
                notice_keys = ["notice_date", "publication_date", "issue_date", "issued_date", "date", "place_and_date"]
                if raw_extract and isinstance(raw_extract, dict):
                    for k in notice_keys:
                        v = raw_extract.get(k)
                        if v and str(v).strip() not in ("", "None", "null"):
                            raw_notice_date = str(v).strip()
                            notice_source_tag = "Footer Date" if "footer" in k or k == "date" else "Place + Date"
                            break

            if not raw_notice_date and flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        for k in notice_keys:
                            v = item.get(k)
                            if v and str(v).strip() not in ("", "None", "null"):
                                raw_notice_date = str(v).strip()
                                notice_source_tag = "Footer Date" if "footer" in k or k == "date" else "Place + Date"
                                break
                        if raw_notice_date:
                            break

            cand_cat = db_dict.get("catalogue_view_date") or db_dict.get("sale_notice_date") or raw_notice_date
            if notice_source_tag:
                cat_view_source = notice_source_tag
            elif db_dict.get("catalogue_view_date") or db_dict.get("sale_notice_date"):
                cat_view_source = "Notice Metadata"

            final_cat_view = format_date_to_dmy(cand_cat) if cand_cat else None
            if not final_cat_view and cand_cat:
                import re
                m_c = re.search(r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b', str(cand_cat))
                if m_c:
                    final_cat_view = format_date_to_dmy(m_c.group(0)) or m_c.group(0)

            # Rule 4 & Rule 5 Validation: Never use Auction/Inspection/Submission/Demand/Possession dates
            formatted_auc_start = record_dict.get("auction_date_time")
            formatted_auc_end = record_dict.get("auction_end_date_time")
            
            # If catalogue_view_date == auction_date_time and source was not valid Notice Metadata, reset to null
            if final_cat_view:
                clean_cat = final_cat_view.split()[0]
                is_invalid = False
                if formatted_auc_start and clean_cat == str(formatted_auc_start).split()[0] and not notice_source_tag:
                    is_invalid = True
                if formatted_auc_end and clean_cat == str(formatted_auc_end).split()[0] and not notice_source_tag:
                    is_invalid = True
                
                if is_invalid:
                    logger.warning("Rule 5 Validation: Resetting catalogue_view_date (%s) to null because source was invalid.", final_cat_view)
                    final_cat_view = None
                    cat_view_source = None

            # Rule 1: Inspection Schedule strictly from explicit Inspection Section
            raw_insp_from_candidate = db_dict.get("inspection_from_date")
            raw_insp_to_candidate = db_dict.get("inspection_to_date")
            
            if not raw_insp_from_candidate and flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        cand = item.get("inspection_schedule_from") or item.get("inspection_schedule_from_date") or item.get("inspection_from_date")
                        if cand and str(cand).strip() not in ("", "None", "null"):
                            raw_insp_from_candidate = cand
                            insp_from_source = "Inspection Schedule"
                            break

            if not raw_insp_to_candidate and flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        cand = item.get("inspection_schedule_to") or item.get("inspection_schedule_to_date") or item.get("inspection_to_date")
                        if cand and str(cand).strip() not in ("", "None", "null"):
                            raw_insp_to_candidate = cand
                            insp_to_source = "Inspection Schedule"
                            break

            if db_dict.get("inspection_from_date"):
                insp_from_source = "Inspection Schedule"
            if db_dict.get("inspection_to_date"):
                insp_to_source = "Inspection Schedule"

            final_insp_from = format_date_to_dmy(raw_insp_from_candidate, include_time=True) if raw_insp_from_candidate and insp_from_source else None
            final_insp_to = format_date_to_dmy(raw_insp_to_candidate, include_time=True) if raw_insp_to_candidate and insp_to_source else None

            # Assign validated dates to record dictionary
            record_dict["catalogue_view_date"] = final_cat_view
            record_dict["inspection_schedule_from_date"] = final_insp_from
            record_dict["inspection_schedule_to_date"] = final_insp_to

            # Filter response fields based on schema
            filtered_record = {k: record_dict[k] for k in schema_fields if k in record_dict}
            if "catalogue_view_date" in schema_fields:
                filtered_record["catalogue_view_date"] = final_cat_view
            if "inspection_schedule_from_date" in schema_fields:
                filtered_record["inspection_schedule_from_date"] = final_insp_from
            if "inspection_schedule_to_date" in schema_fields:
                filtered_record["inspection_schedule_to_date"] = final_insp_to

            # Rule 6: Source Tracking internal logging (do not add to API payload)
            safe_print_local("\n=== DATE FIELD TRACING LOGS (INTERNAL VALIDATION) ===")
            safe_print_local(f"  catalogue_view_date            <- {final_cat_view} ({cat_view_source or 'None'})")
            safe_print_local(f"  inspection_schedule_from_date <- {final_insp_from} ({insp_from_source or 'None'})")
            safe_print_local(f"  inspection_schedule_to_date   <- {final_insp_to} ({insp_to_source or 'None'})")
            safe_print_local(f"  auction_date_time             <- {record_dict.get('auction_date_time')} ({auc_date_source})")
            safe_print_local("======================================================\n")

            records_dict.append(filtered_record)
        elif isinstance(record, dict):
            rec_copy = dict(record)
            cat_val = rec_copy.get("catalogue_view_date") or rec_copy.get("sale_notice_date")
            if not cat_val and flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        found = item.get("catalogue_view_date") or item.get("notice_date") or item.get("publication_date") or item.get("date") or item.get("place_and_date")
                        if found:
                            cat_val = found
                            break
            final_val = format_date_to_dmy(cat_val) if cat_val else None
            if not final_val and cat_val:
                import re
                match = re.search(r'\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b', str(cat_val))
                if match:
                    final_val = format_date_to_dmy(match.group(0)) or match.group(0)
                else:
                    final_val = str(cat_val).strip()
            rec_copy["catalogue_view_date"] = final_val or None

            insp_from_val = rec_copy.get("inspection_schedule_from_date") or rec_copy.get("inspection_schedule_from")
            insp_to_val = rec_copy.get("inspection_schedule_to_date") or rec_copy.get("inspection_schedule_to")
            if not insp_from_val and flat_raw_extracts:
                for item in flat_raw_extracts:
                    if isinstance(item, dict):
                        f_date = item.get("inspection_schedule_from") or item.get("inspection_schedule_from_date") or item.get("inspection_from_date")
                        t_date = item.get("inspection_schedule_to") or item.get("inspection_schedule_to_date") or item.get("inspection_to_date")
                        if f_date:
                            insp_from_val = f_date
                        if t_date:
                            insp_to_val = t_date
                        if f_date or t_date:
                            break
            if "inspection_schedule_from_date" in rec_copy:
                rec_copy["inspection_schedule_from_date"] = format_date_to_dmy(insp_from_val) if insp_from_val else None
            if "inspection_schedule_to_date" in rec_copy:
                rec_copy["inspection_schedule_to_date"] = format_date_to_dmy(insp_to_val) if insp_to_val else None

            records_dict.append(rec_copy)
        else:
            records_dict.append(record)

    error_msg = None
    if len(records_dict) == 0 and "extraction_results" in result:
        for res in result["extraction_results"]:
            if not res.get("success") and res.get("message"):
                error_msg = res["message"]
                break

    response = {
        "success": len(records_dict) > 0 or result["summary"]["total_notices"] == 0,
        "upload_id": result["upload"].id,
        "upload_number": result["upload"].upload_number,
        "total_records": len(records_dict),
        "records": records_dict,
        "summary": result["summary"],
    }

    if error_msg:
        response["message"] = error_msg

    # Step 5: Log final API response
    import sys
    def safe_print(text: str):
        try:
            sys.stdout.write(str(text).encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8", errors="replace") + "\n")
        except Exception:
            try:
                print(str(text).encode("ascii", errors="replace").decode("ascii"))
            except Exception:
                pass

    safe_print("\n=== STEP 5: FINAL API RESPONSE ===")
    import json
    from decimal import Decimal
    from pathlib import Path
    class SafeDecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, Path):
                return str(obj)
            return super(SafeDecimalEncoder, self).default(obj)
    try:
        safe_print(json.dumps(response, indent=2, cls=SafeDecimalEncoder))
    except Exception as e:
        safe_print(f"Error printing response: {e}")
        safe_print(response)
    safe_print("===================================\n")

    return response
