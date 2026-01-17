"""
Data extraction utilities for workflows.
"""

import re
from typing import Optional, Tuple


def extract_phone_number(text: str) -> Optional[str]:
    """Extract Kenyan phone number from text."""
    # Kenyan phone patterns: 07xx, 01xx, +254, 254
    patterns = [
        r"\b(254)?([17]\d{8})\b",  # 254712345678 or 712345678
        r"\b\+?(254)([17]\d{8})\b",  # +254712345678
        r"\b(0[17]\d{8})\b",  # 0712345678
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            if len(match.groups()) == 2:
                prefix, number = match.groups()
                if prefix == "254":
                    return f"254{number}"
                else:
                    return (
                        f"254{number[1:]}" if number.startswith("0") else f"254{number}"
                    )
            else:
                number = match.group(0)
                if number.startswith("0"):
                    return f"254{number[1:]}"
                return number.replace("+", "")

    return None


def extract_fleet_number(text: str) -> Optional[str]:
    """Extract fleet number from text (format: XX00)."""
    pattern = r"\b([a-zA-Z]{2}\d{2,4})\b"
    match = re.search(pattern, text.lower())
    return match.group(1).upper() if match else None


def extract_amount(text: str) -> Optional[float]:
    """Extract monetary amount from text."""
    # Match patterns like: 500, KSh 500, 500 KSh, Ksh500
    pattern = r"(?:ksh?\.?\s*)?(\d+(?:,\d{3})*(?:\.\d{2})?)"
    match = re.search(pattern, text.lower())
    if match:
        amount_str = match.group(1).replace(",", "")
        return float(amount_str)
    return None


def extract_location_pair(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract origin and destination from text."""
    # Patterns: "from X to Y", "X to Y"
    patterns = [
        r"from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s|$|\.)",
        r"([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:\s|$|\.)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            origin = match.group(1).strip().title()
            destination = match.group(2).strip().title()
            return origin, destination

    return None, None
