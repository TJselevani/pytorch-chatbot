import re

def extract_phone_number(message: str):
    """Extracts a 10-digit phone number from the message if present."""
    match = re.search(r'(\d{10})', message)
    return match.group(1) if match else None

def extract_fleet_number(message: str):
    """Extracts fleet numbers (seXX format) from the message."""
    match = re.search(r'(se\d+)', message, re.IGNORECASE)
    return match.group(1).lower() if match else None

def extract_transfer_details(message: str):
    """ Extracts amount, source and destination """
    return re.search(r'transfer\s+for\s+me\s+ksh\s+(\d+)\s+from\s+(se\d+)\s+to\s+(se\d+)', message, re.IGNORECASE)

