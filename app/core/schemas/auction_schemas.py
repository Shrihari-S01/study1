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
    "emd_bank_name", "emd_account_number", "emd_ifsc", "borrower", "auction_office", "institution_seller",
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
    "emd_bank_name", "emd_account_number", "emd_ifsc", "borrower", "remarks", "authorized_officer_name",
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
    s_val = str(val).strip()
    if not s_val or s_val.startswith("0000") or s_val.lower() in {"null", "none", "n/a", "undefined"}:
        return None
    try:
        if isinstance(val, (datetime, date)):
            dt = val
        else:
            import dateutil.parser, re
            clean_s = re.sub(r"(?i)\b(by|at|before|from|to)\b", " ", s_val)
            clean_s = re.sub(r"\s+", " ", clean_s).strip()
            dt = dateutil.parser.parse(clean_s)
        if include_time:
            return dt.strftime("%d-%m-%Y %H:%M")
        else:
            return dt.strftime("%d-%m-%Y")
    except Exception:
        import re, dateutil.parser
        m = re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", s_val)
        if m:
            try:
                dt = dateutil.parser.parse(m.group(0))
                return dt.strftime("%d-%m-%Y")
            except Exception:
                return m.group(0)
        return s_val if not s_val.startswith("0000") else None

def clean_numeric(val):
    if val in (None, ""):
        return None
    try:
        if isinstance(val, (int, float, Decimal)):
            return float(val)
        import re
        s = str(val).strip()
        s = re.sub(r"(?i)\b(rs|inr|rupees)\b\.?\s*", "", s)
        s = s.replace("₹", "").replace("Rs", "").replace("rs", "").rstrip("/-").replace(",", "").strip()
        if s:
            return float(s)
        return None
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

    records_to_process = result.get("results") or result.get("auctions") or []
    for idx, record in enumerate(records_to_process):
        if hasattr(record, "__table__"):
            db_dict = {c.key: getattr(record, c.key) for c in record.__table__.columns}
        elif isinstance(record, dict):
            db_dict = dict(record)
        else:
            db_dict = {}
            
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
            schema_fields = PROPERTY_FIELDS
            schema_name = "PROPERTY_SCHEMA"

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

        # Pass db_dict and raw extracts through CommonAISchemaBuilder for complete alias resolution
        from app.services.integration.schema_builder import CommonAISchemaBuilder
        from app.services.integration.normalizer import DataNormalizer
        
        common_extract = CommonAISchemaBuilder.build_schema(db_dict)
        if raw_extract and isinstance(raw_extract, dict):
            raw_cand = CommonAISchemaBuilder.build_schema(raw_extract)
            for k, v in raw_cand.items():
                if v and not common_extract.get(k):
                    common_extract[k] = v
        
        if flat_raw_extracts:
            for item in flat_raw_extracts:
                if isinstance(item, dict):
                    cand = CommonAISchemaBuilder.build_schema(item)
                    for k, v in cand.items():
                        if v and not common_extract.get(k):
                            common_extract[k] = v

        # Build clean records mapping dict
        record_dict = {field: None for field in schema_fields}

        record_dict["asset_type"] = asset_type_normalized
        record_dict["asset_category"] = category or None

        # Sanitize auction_no: Never allow Seller Name to populate auction_no
        raw_auc_no = str(db_dict.get("auction_no") or common_extract.get("auction_number") or db_dict.get("auction_number") or db_dict.get("p_auction_number") or "").strip()
        seller_str = str(db_dict.get("institution_seller") or common_extract.get("seller_name") or "").strip()
        if raw_auc_no and (len(raw_auc_no) > 15 or (seller_str and raw_auc_no.lower() in seller_str.lower())):
            record_dict["auction_no"] = str(db_dict.get("lot_no") or str(idx + 1).zfill(2))
        else:
            record_dict["auction_no"] = raw_auc_no or str(db_dict.get("lot_no") or "") or str(idx + 1).zfill(2)

        raw_desc = db_dict.get("auction_description") or common_extract.get("description") or None
        if isinstance(raw_desc, list):
            items_str = []
            for itm in raw_desc:
                if isinstance(itm, dict):
                    parts = []
                    name_part = itm.get("item") or itm.get("item_description") or itm.get("description") or itm.get("property_description")
                    if name_part:
                        parts.append(str(name_part))
                    if itm.get("make"):
                        parts.append(f"Make {itm['make']}")
                    if itm.get("model"):
                        parts.append(f"Model {itm['model']}")
                    if itm.get("capacity"):
                        parts.append(f"Capacity {itm['capacity']}")
                    if itm.get("year_of_manufacturing"):
                        parts.append(f"manufactured in {itm['year_of_manufacturing']}")
                    if parts:
                        items_str.append(", ".join(parts))
                elif isinstance(itm, str):
                    items_str.append(itm)
            record_dict["auction_description"] = ". ".join(items_str) if items_str else None
        elif isinstance(raw_desc, dict):
            parts = []
            name_part = raw_desc.get("item") or raw_desc.get("item_description") or raw_desc.get("description") or raw_desc.get("property_description")
            if name_part:
                parts.append(str(name_part))
            if raw_desc.get("make"):
                parts.append(f"Make {raw_desc['make']}")
            if raw_desc.get("model"):
                parts.append(f"Model {raw_desc['model']}")
            if raw_desc.get("capacity"):
                parts.append(f"Capacity {raw_desc['capacity']}")
            if raw_desc.get("year_of_manufacturing"):
                parts.append(f"manufactured in {raw_desc['year_of_manufacturing']}")
            if not parts:
                parts = [f"{k} {v}" for k, v in raw_desc.items() if v and k not in {"value_in_inr", "total_value_in_inr"}]
            record_dict["auction_description"] = ", ".join(parts) if parts else None
        else:
            record_dict["auction_description"] = str(raw_desc) if raw_desc else None

        # Hard Sanitizer: Stage 6 Canonical Location Reconciliation
        def clean_location_str(val):
            if not val:
                return None
            v_str = str(val).strip()
            if v_str.startswith("[") or v_str.startswith("{"):
                try:
                    import json
                    parsed = json.loads(v_str)
                    return normalize_location_obj(parsed)
                except Exception:
                    return None
            forbidden = [
                "property_no:", "description:", "area_hectares:", "value_in_inr:",
                "quantity:", "model:", "year_of_manufacturing:", "make:", "item:"
            ]
            lower_v = v_str.lower()
            if any(x in lower_v for x in forbidden):
                return None
            import re
            v_str = re.sub(r"(?i)^(location|place|situated\s+at|located\s+at)\s*[:\-]\s*", "", v_str).strip()
            v_str = v_str.strip("[]{}() ")
            return v_str or None

        def normalize_location_obj(val):
            if val is None:
                return None
            if isinstance(val, dict):
                loc = val.get("location") or val.get("address") or val.get("asset_location") or val.get("product_location")
                return clean_location_str(loc)
            if isinstance(val, list):
                locs = []
                for item in val:
                    if isinstance(item, dict):
                        loc = item.get("location") or item.get("address") or item.get("asset_location") or item.get("product_location")
                        if loc:
                            locs.append(str(loc).strip())
                    elif isinstance(item, str):
                        locs.append(item.strip())
                cleaned = []
                for x in locs:
                    cx = clean_location_str(x)
                    if cx and cx not in cleaned:
                        cleaned.append(cx)
                return "; ".join(cleaned) if cleaned else None
            if isinstance(val, str):
                return clean_location_str(val)
            return None

        raw_loc = db_dict.get("assets_location") or db_dict.get("location") or common_extract.get("asset_location") or None
        record_dict["assets_location"] = normalize_location_obj(raw_loc)

        # Notice bank details and branch office department mapping
        bank_val = db_dict.get("institution_seller") or common_extract.get("seller_name") or None
        if "institution_seller" in record_dict:
            record_dict["institution_seller"] = bank_val
        
        if "auction_office" in record_dict:
            record_dict["auction_office"] = db_dict.get("auction_office") or db_dict.get("auction_office_department") or db_dict.get("branch_name") or None
        if "auction_department" in record_dict:
            record_dict["auction_department"] = db_dict.get("auction_department") or db_dict.get("auction_office_department") or None

        # Borrower mapping with M/s legal abbreviation restoration
        bor_val = db_dict.get("borrower") or db_dict.get("borrower_name") or common_extract.get("borrower_name") or None
        if bor_val:
            bor_val = DataNormalizer.restore_legal_abbreviations(str(bor_val))
        if "borrower" in record_dict:
            record_dict["borrower"] = bor_val

        # EMD details mapping
        emd_bank = db_dict.get("emd_bank_name") or common_extract.get("emd_bank_name")
        emd_acc = db_dict.get("emd_account_no") or db_dict.get("emd_account_number") or common_extract.get("emd_account_no")
        emd_ifsc_val = db_dict.get("emd_ifsc") or db_dict.get("ifsc") or common_extract.get("emd_ifsc")

        if "emd_bank_name" in record_dict:
            record_dict["emd_bank_name"] = emd_bank or None
        if "emd_account_number" in record_dict:
            record_dict["emd_account_number"] = emd_acc or None
        if "emd_ifsc" in record_dict:
            record_dict["emd_ifsc"] = emd_ifsc_val or None

        # Numeric price conversions & Authoritative Reserve Price Alias Propagation
        raw_reserve = db_dict.get("reserve_price") or db_dict.get("reserver_price") or db_dict.get("p_reserver_price") or common_extract.get("reserve_price")
        raw_starting = db_dict.get("starting_price") or db_dict.get("auction_start_price") or common_extract.get("starting_price")

        clean_reserve = clean_numeric(raw_reserve)
        clean_starting = clean_numeric(raw_starting)

        final_price = None
        if clean_reserve not in (None, "", 0, 0.0):
            final_price = clean_reserve
        elif clean_starting not in (None, "", 0, 0.0):
            final_price = clean_starting

        record_dict["starting_price"] = final_price
        record_dict["reserve_price"] = final_price
        record_dict["reserver_price"] = final_price
        record_dict["p_reserver_price"] = final_price
        record_dict["auction_start_price"] = final_price

        emd_val = clean_numeric(db_dict.get("emd_price") or db_dict.get("emd_amount") or common_extract.get("emd_amount"))
        record_dict["pre_bid_emd"] = emd_val
        record_dict["emd_price"] = emd_val
        record_dict["emd_amount"] = emd_val

        inc_val = clean_numeric(db_dict.get("increment_price") or db_dict.get("bid_increment") or common_extract.get("increment_price"))
        record_dict["increment_price"] = inc_val
        record_dict["bid_increment"] = inc_val

        record_dict["currency"] = db_dict.get("currency") or common_extract.get("currency") or "INR"

        # Direct Field Serialization (Preserve extracted values dynamically)
        record_dict["auction_type"] = db_dict.get("auction_type") or common_extract.get("auction_type") or None
        record_dict["auto_extension"] = db_dict.get("auto_extension") or common_extract.get("auto_extension") or None
        record_dict["auto_extension_mode"] = db_dict.get("auto_extension_mode") or common_extract.get("auto_extension_mode") or None
        record_dict["auction_live_status"] = db_dict.get("auction_live_status") or common_extract.get("auction_live_status") or "Pending"
        record_dict["first_bid_acceptance_condition"] = db_dict.get("first_bid_acceptance_condition") or common_extract.get("first_bid_acceptance_condition") or None
        record_dict["digital_certificate"] = db_dict.get("digital_certificate") or common_extract.get("digital_certificate") or None
        record_dict["asset_subcategory"] = db_dict.get("asset_subcategory") or common_extract.get("asset_category") or None
        record_dict["vendor_name"] = db_dict.get("vendor_name") or common_extract.get("seller_name") or None
        record_dict["event_type"] = db_dict.get("event_type") or common_extract.get("auction_type") or None
        record_dict["payment_type"] = db_dict.get("payment_type") or None

        record_dict["inspection_schedule_from_date"] = format_date_to_dmy(db_dict.get("inspection_from_date") or common_extract.get("inspection_from_date"), include_time=True)
        record_dict["inspection_schedule_to_date"] = format_date_to_dmy(db_dict.get("inspection_to_date") or common_extract.get("inspection_to_date"), include_time=True)
        record_dict["catalogue_view_date"] = format_date_to_dmy(db_dict.get("catalogue_view_date") or common_extract.get("catalogue_view_date"))

        record_dict["auction_date_time"] = format_date_to_dmy(
            db_dict.get("auction_start_datetime") or db_dict.get("auction_date_time") or common_extract.get("auction_start_datetime") or common_extract.get("auction_date_time"),
            include_time=True
        )
        record_dict["auction_end_date_time"] = format_date_to_dmy(
            db_dict.get("auction_end_datetime") or db_dict.get("auction_end_date_time") or common_extract.get("auction_end_datetime") or common_extract.get("auction_end_date_time"),
            include_time=True
        )
        record_dict["submit_application"] = format_date_to_dmy(db_dict.get("submit_application") or common_extract.get("submit_application"), include_time=True)
        record_dict["repo_date"] = format_date_to_dmy(db_dict.get("repo_date"))

        # Remarks & Officer details
        if "remarks" in record_dict:
            record_dict["remarks"] = db_dict.get("remarks") or common_extract.get("remarks") or None
        if "authorized_officer_name" in record_dict:
            record_dict["authorized_officer_name"] = db_dict.get("authorized_officer_name") or common_extract.get("authorized_officer_name") or None
        if "authorized_officer_number" in record_dict:
            record_dict["authorized_officer_number"] = db_dict.get("authorized_officer_number") or common_extract.get("authorized_officer_number") or None

        # Filter response fields based on schema
        filtered_record = {k: record_dict[k] for k in schema_fields if k in record_dict}

        records_dict.append(filtered_record)

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
