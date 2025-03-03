import os
import sys
from utils.context import user_context
from utils.extractors import extract_phone_number, extract_fleet_number

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def handle_driver_request(bot_name, user_id, message):
    """Handles OTP and transfer requests separately before running intent classification."""
    
    # Check for OTP request
    if "OTP" in message or "Sipati" in message:
        phone_number = extract_phone_number(message)
        if phone_number:
            return {bot_name: "Kindly wait as your request is being processed."}
        else:
            user_context[user_id] = "awaiting_fleet_number"
            return {bot_name: "Sawa, kindly help me with your fleet number."}

    # If waiting for fleet number
    if user_context.get(user_id) == "awaiting_fleet_number":
        fleet_number = extract_fleet_number(message)
        if fleet_number:
            user_context.pop(user_id)  # Clear context
            return {bot_name: "Kindly wait as your request is being processed."}
        else:
            return {bot_name: "Please provide a valid fleet number."}

    # Handle cash transfer request
    if "Transfer" in message:
        match = re.search(r'Transfer for me ksh (\d+) from (se\d+) to (se\d+)', message)
        if match:
            amount, source_fleet, destination_fleet = match.groups()
            return {bot_name: "Okay, Kindly wait as your request is being processed."}

    return None  # Return None if no special handling was needed
