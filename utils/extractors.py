import re

def extract_phone_number(message: str):
    """Extracts a 10-digit phone number from the message if present."""
    match = re.search(r'(\+254\d{9}|\d{12}|0\d{9}|\d{10})', message)
    return match.group(1) if match else None

def extract_fleet_number(message: str):
    """Extracts fleet numbers (seXX format) from the message."""
    match = re.search(r'(se\d+|sm\d+)', message, re.IGNORECASE)
    return match.group(1).lower() if match else None

def extract_transfer_details(message: str):
    """ Extracts amount, source and destination """
    return re.search(r'transfer\s+for\s+me\s+ksh\s+(\d+)\s+from\s+(se\d+)\s+to\s+(se\d+)', message, re.IGNORECASE)


# import re

# def extract_phone_number(message: str):
#     """Extracts a phone number from the message if present.
#     Supports formats: 0700000000, +254700000000, 254700000000."""
#     # Regular expression pattern to match the phone number formats
#     pattern = r'(\+254\d{9}|\d{12}|0\d{9})'
    
#     match = re.search(pattern, message)
#     return match.group(1) if match else None

# def extract_fleet_number(message: str):
#     """Extracts fleet numbers (seXX or smXX format) from the message."""
#     # Regular expression pattern to match both 'se' and 'sm' formats
#     pattern = r'(se\d+|sm\d+)', re.IGNORECASE
    
#     match = re.search(pattern, message, re.IGNORECASE)
#     return match.group(1).lower() if match else None

# def extract_transfer_details(message: str):
#     """ Extracts amount, source and destination """
#     return re.search(r'transfer\s+for\s+me\s+ksh\s+(\d+)\s+from\s+(se\d+)\s+to\s+(se\d+)', message, re.IGNORECASE)

