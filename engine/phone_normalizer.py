"""
Luxe Wave KSA Phone Normalizer & Validator.
Normalizes Saudi mobile and landline numbers for enterprise B2B hospitality procurement:
Standard format: +9665XXXXXXXX or 05XXXXXXXX.
Handles Arabic-Indic, Persian, international formats, and spaces.
"""
import re

ARABIC_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
EASTERN_ARABIC_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

VALID_KSA_MOBILE_PREFIXES = ("050", "053", "054", "055", "056", "057", "058", "059")

class KsaPhoneValidationError(ValueError):
    """Raised when phone number is invalid for Saudi Arabia."""
    pass

def normalize_ksa_phone(raw_phone: str) -> str:
    """
    Normalizes any KSA phone input into clean 10-digit format (05XXXXXXXX)
    or international standard (+9665XXXXXXXX).
    """
    if not raw_phone or not isinstance(raw_phone, str):
        raise KsaPhoneValidationError("Phone number is required and must be a valid string")

    # Step 1: Normalize Arabic/Indic digits
    clean = raw_phone.translate(ARABIC_INDIC_DIGITS).translate(EASTERN_ARABIC_DIGITS)
    # Step 2: Strip non-digits
    digits = re.sub(r"\D", "", clean)

    if not digits:
        raise KsaPhoneValidationError("Phone number contains no valid digits")

    # Step 3: Handle international prefix
    if digits.startswith("00966"):
        digits = digits[5:]
    elif digits.startswith("966"):
        digits = digits[3:]

    # Step 4: Add leading zero if 9 digits starting with 5
    if len(digits) == 9 and digits.startswith("5"):
        digits = "0" + digits

    # Step 5: Check length and prefix
    if len(digits) != 10:
        raise KsaPhoneValidationError(f"KSA mobile number must be 10 digits (got {len(digits)} digits: {digits})")

    if not digits.startswith(VALID_KSA_MOBILE_PREFIXES):
        raise KsaPhoneValidationError(f"KSA mobile number must start with a valid 05X prefix (got: {digits[:3]})")

    return digits

def format_ksa_international(normalized_local: str) -> str:
    """Converts 05XXXXXXXX to +9665XXXXXXXX for WhatsApp API and CRM."""
    if normalized_local.startswith("0"):
        return "+966" + normalized_local[1:]
    return "+966" + normalized_local
