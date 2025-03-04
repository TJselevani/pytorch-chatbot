import os
import sys
from utils.context import user_context
from utils.extractors import extract_phone_number, extract_fleet_number, extract_transfer_details
from utils.match import is_match, is_pattern, detect_language

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Function to get the response in the detected language
def get_response_text(language, key):
    responses = {
        "awaiting_fleet_number": {
            "en": "Okay, kindly help me with your fleet number.",
            "sw": "Sawa, tafadhali nisaidie na nambari ya gari lako."
        },
        "invalid_fleet_number": {
            "en": "Please provide a valid fleet number.",
            "sw": "Tafadhali nisaidie nambari sahihi ya gari lako"
        },
        "processing_request": {
            "en": "Kindly wait as your request is being processed.",
            "sw": "Tafadhali subiri ombi lako linashughulikiwa."
        },
        "default": {
            "en": "I'm sorry, I didn't understand that.",
            "sw": "Samahani, sijaelewa."
        }

    }
    return responses.get(key, {}).get(language, responses[key]["en"])  # Default to English if language key is missing


def handle_driver_request(bot_name, user_id, message):
    """Handles OTP and transfer requests separately before running intent classification."""
     # Detect message language
    language = detect_language(message)
    
    # Check for OTP request
    keywords = ["otp", "sipati"]

    if any(is_match(word, message) for word in keywords):
        phone_number = extract_phone_number(message)
        if phone_number:
            print("Phone number found: ", phone_number)
            return {bot_name: get_response_text(language, "processing_request")}
        else:
            # user_context[user_id] = "awaiting_fleet_number"
            user_context[user_id]["awaiting_fleet_number"] = True 
            return {bot_name: get_response_text(language, "awaiting_fleet_number")}

    # If waiting for fleet number
    if user_context.get(user_id, {}).get("awaiting_fleet_number"):
        fleet_number = extract_fleet_number(message)
        if fleet_number:
            user_context[user_id].pop("awaiting_fleet_number")  # Clear the flag after receiving fleet number
            print("Fleet number found: ", fleet_number)
            return {bot_name: get_response_text(language, "processing_request")}
        else:
            return {bot_name: get_response_text(language, "invalid_fleet_number")}

    # Handle cash transfer request
    if is_pattern(message, "transfer", "from", "to"):
        match = extract_transfer_details(message)
        if match:
            amount, source_fleet, destination_fleet = match.groups()
            print(f'Transferring ksh {amount} from {source_fleet} to {destination_fleet}')
            return {bot_name: get_response_text(language, "processing_request")}

    return None  # Return None if no special handling was needed
