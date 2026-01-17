"""
Input validation utilities.
"""

import re

# from typing import Dict, Any


class ValidationError(Exception):
    """Custom validation error."""

    pass


def validate_phone_number(phone: str) -> bool:
    """Validate Kenyan phone number format."""
    pattern = r"^(254|0)?[17]\d{8}$"
    return bool(re.match(pattern, phone))


def validate_fleet_number(fleet: str) -> bool:
    """Validate fleet number format."""
    pattern = r"^[A-Z]{2}\d{2,4}$"
    return bool(re.match(pattern, fleet.upper()))


def validate_amount(amount: float) -> bool:
    """Validate transfer amount."""
    return 0 < amount <= 1000000  # Max 1M KSh


def validate_otp_code(otp: str) -> bool:
    """Validate OTP code format."""
    return bool(re.match(r"^\d{4,6}$", otp))
