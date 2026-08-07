"""
Payload Sanitizer & Control Character Cleaner.

Recursively cleans and sanitizes strings, dictionaries, and lists:
- Removes null bytes (\x00), invalid control characters (\x00-\x1f, except space).
- Replaces carriage returns (\r), tabs (\t), and raw unescaped newlines with clean single spaces.
- Preserves valid Unicode text.
- Validates JSON serializability and reports exact failing field names.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Tuple
from app.core.logger import get_logger

logger = get_logger(__name__)


def sanitize_varchar_field(value: Any) -> str:
    r"""
    Sanitize a single VARCHAR/TEXT field specifically for PHP database insertion:
    - Removes ASCII control characters (\x00-\x1f, \x7f-\x9f).
    - Replaces \r, \n, \t, \v, \f with clean single spaces.
    - Removes SQL-breaking characters from the PHP payload only (' " ` \).
    - Preserves letters, numbers, spaces, and allowed symbols (/ - . , : & () % # + _ @ ; ? = * !).
    - Collapses multiple consecutive spaces into a single space.
    - Trims leading/trailing whitespace.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)

    # 1. Replace carriage returns (\r), newlines (\n), tabs (\t), vertical tabs (\v), form feeds (\f), null bytes (\x00) with single spaces
    s = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ").replace("\t", " ").replace("\v", " ").replace("\f", " ").replace("\x00", " ")

    # 2. Strip unprintable ASCII control characters (\x00-\x1f, \x7f-\x9f)
    s = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", s)

    # 3. Remove typographic quotes & SQL-breaking characters (' " ` \) from PHP payload
    s = s.replace("“", "").replace("”", "").replace("‘", "").replace("’", "")
    s = s.replace("'", "").replace('"', '').replace("`", "").replace("\\", "")

    # 4. Replace non-breaking spaces with normal space
    s = s.replace("\u00a0", " ")

    # 5. Collapse multiple consecutive spaces into a single space
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def sanitize_string_field(value: Any) -> str:
    """
    Sanitize a single text string using sanitize_varchar_field.
    """
    return sanitize_varchar_field(value)


def sanitize_json_payload(data: Any) -> Any:
    """
    Recursively sanitize dictionaries, lists, and strings for 100% safe JSON serialization.
    """
    if data is None:
        return ""
    if isinstance(data, str):
        return sanitize_varchar_field(data)
    if isinstance(data, dict):
        return {sanitize_varchar_field(k): sanitize_json_payload(v) for k, v in data.items()}
    if isinstance(data, (list, tuple, set)):
        return [sanitize_json_payload(item) for item in data]
    if isinstance(data, (int, float, bool)):
        return data
    return sanitize_varchar_field(str(data))


class PHPSanitizer:
    r"""
    Dedicated Schema-Driven PHP Payload Normalizer & Validation Framework.
    
    1. Keeps original extracted data unchanged by creating a new payload object for PHP.
    2. Accepts multiple semantic inputs for ENUM fields and normalizes them dynamically.
    3. Schema-driven: Supports ENUM, VARCHAR, TEXT, INTEGER, DATE, DATETIME, DECIMAL via PHP_SCHEMA_SPEC.
    4. Produces detailed audit logs per field:
       Field Name
       Expected Type
       Allowed Values
       Incoming Value
       Normalized Value
       Validation Result
    5. Rejects any invalid enum or schema-failing field before calling PHP API.
    """

    @classmethod
    def sanitize_and_validate_payload(
        cls,
        payload: Dict[str, Any],
        processing_id: str = "N/A"
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Creates a new, fully sanitized & schema-validated payload object specifically for PHP insertion.
        Original payload dict is NOT mutated.
        
        Returns:
            Tuple[sanitized_payload, is_valid, validation_errors]
        """
        if not isinstance(payload, dict):
            return {}, False, ["Payload must be a dictionary"]

        from app.services.integration.php_payload_normalizer import PHP_SCHEMA_SPEC, CentralizedPHPPayloadNormalizer

        sanitized_payload: Dict[str, Any] = {}
        validation_errors: List[str] = []

        logger.info("\n================================================================================")
        logger.info("[%s] SCHEMA-DRIVEN PHP PAYLOAD NORMALIZATION & VALIDATION REPORT", processing_id)
        logger.info("================================================================================")

        # Guarantee all schema spec fields are processed and never omitted from sanitized_payload
        field_keys = list(payload.keys())
        for spec_field in PHP_SCHEMA_SPEC:
            if spec_field not in field_keys:
                field_keys.append(spec_field)

        for field_name in field_keys:
            orig_val = payload.get(field_name)
            spec = PHP_SCHEMA_SPEC.get(field_name, {"type": "VARCHAR", "max_length": 255, "required": False, "default": ""})
            is_req = spec.get("required", False)
            default_val = spec.get("default", "")

            if orig_val is None or str(orig_val).strip() == "":
                fallback_val = default_val if default_val is not None else ""
                sanitized_payload[field_name] = fallback_val
                if is_req:
                    validation_errors.append(f"Field '{field_name}': Mandatory required field is missing or empty")
                continue

            orig_str = str(orig_val)
            orig_len = len(orig_str)

            spec = PHP_SCHEMA_SPEC.get(field_name, {"type": "VARCHAR", "max_length": 255})
            expected_type = spec.get("type", "VARCHAR").upper()
            max_len = spec.get("max_length", 255)
            allowed_values = spec.get("allowed_values")
            allowed_repr = str(allowed_values) if allowed_values is not None else "N/A"

            # Step 1: Base VARCHAR sanitization for all text fields
            clean_input = orig_val
            if isinstance(orig_val, str) or expected_type in {"VARCHAR", "TEXT", "REMARKS", "PHONE", "ACCOUNT_NO", "IFSC", "BANK_NAME"}:
                clean_input = sanitize_varchar_field(orig_val)

            # Step 2: Schema spec conversion & field-specific normalization
            converted_val, val_status = CentralizedPHPPayloadNormalizer.convert_value_by_spec(field_name, clean_input, spec)

            # Step 3: Final pass for VARCHAR string cleanups
            if isinstance(converted_val, str) and expected_type not in {"ENUM"}:
                converted_val = sanitize_varchar_field(converted_val)
                if len(converted_val) > max_len:
                    converted_val, trans = CentralizedPHPPayloadNormalizer.generic_intelligent_shorten(converted_val, max_len)
                    converted_val = sanitize_varchar_field(converted_val)
                    val_status = "TRUNCATED"

            if val_status.startswith("REJECTED"):
                validation_errors.append(f"Field '{field_name}': {val_status}")

            final_len = len(str(converted_val))
            sanitized_payload[field_name] = converted_val

            # Requirement 5: Detailed logging output
            logger.info(
                "Field Name             : %s\n"
                "Expected Type          : %s\n"
                "Allowed Values         : %s\n"
                "Original Value         : %s\n"
                "Normalized Value       : %s\n"
                "Final PHP Payload Value: %s\n"
                "Validation Result      : %s\n"
                "--------------------------------------------------------------------------------",
                field_name,
                expected_type,
                allowed_repr,
                repr(orig_str[:100]),
                repr(str(converted_val)[:100]),
                repr(str(converted_val)[:100]),
                val_status,
            )

        is_valid = len(validation_errors) == 0
        logger.info("Validation Summary: %s\n================================================================================\n", "PASSED" if is_valid else f"FAILED ({len(validation_errors)} errors)")
        return sanitized_payload, is_valid, validation_errors

    @classmethod
    def sanitize_payload(cls, payload: Dict[str, Any], processing_id: str = "N/A") -> Dict[str, Any]:
        """
        Creates a new, fully sanitized payload object specifically for PHP insertion.
        Original payload dict is NOT mutated.
        """
        sanitized_payload, _, _ = cls.sanitize_and_validate_payload(payload, processing_id=processing_id)
        return sanitized_payload


def validate_and_serialize_json_payload(payload: Dict[str, Any], processing_id: str = "N/A") -> Tuple[Dict[str, Any], str]:
    """
    Sanitize and validate payload JSON serializability.
    Logs the final serialized JSON using ensure_ascii=False.
    Raises ValueError with the exact field name if serialization fails.
    """
    sanitized_dict = PHPSanitizer.sanitize_payload(payload, processing_id=processing_id)

    if not isinstance(sanitized_dict, dict):
        sanitized_dict = {"data": sanitized_dict}

    # Validate each key individually to pinpoint exact field if serialization fails
    for field_name, field_value in sanitized_dict.items():
        try:
            json.dumps(field_value, ensure_ascii=False)
        except Exception as field_err:
            logger.error("[%s] JSON serialization error in field '%s': %s", processing_id, field_name, field_err)
            raise ValueError(f"Invalid control character or non-serializable value in field '{field_name}': {str(field_err)}") from field_err

    # Diagnostic Audit: Inspect text fields for special characters (' " \ \n \t) to verify safe parameter binding
    special_char_fields = []
    for field_name, field_value in sanitized_dict.items():
        if isinstance(field_value, str):
            if any(ch in field_value for ch in ["'", '"', "\\", "\n", "\t", "`"]):
                special_char_fields.append((field_name, repr(field_value[:80])))

    if special_char_fields:
        logger.info(
            "\n==================================================\n"
            "[%s] PARAMETER BINDING AUDIT: SPECIAL CHARACTERS DETECTED\n"
            "The following text fields contain quotes or special characters.\n"
            "These fields will be dispatched as bound JSON parameter values (NOT string concatenated):\n%s\n"
            "==================================================",
            processing_id,
            "\n".join(f"  - {k}: {v}" for k, v in special_char_fields)
        )

    try:
        json_str = json.dumps(sanitized_dict, indent=2, ensure_ascii=False)
        logger.info("[%s] FINAL SANITIZED JSON PAYLOAD VALIDATED:\n%s", processing_id, json_str)
        return sanitized_dict, json_str
    except Exception as exc:
        logger.exception("[%s] Invalid JSON payload during full dump: %s", processing_id, exc)
        raise exc

