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
        "awaiting_phone_number": {
            "en": "Kindly provide your phone number.",
            "sw": "Tafadhali toa nambari yako ya simu."
        },
        "awaiting_both": {
            "en": "Please provide both your phone number and fleet number.",
            "sw": "Tafadhali toa nambari yako ya simu na nambari ya gari lako."
        },
        "processing_request": {
            "en": "Kindly wait as your request is being processed.",
            "sw": "Tafadhali subiri ombi lako linashughulikiwa."
        },
        "invalid_fleet_number": {
            "en": "Please provide a valid fleet number.",
            "sw": "Tafadhali nisaidie nambari sahihi ya gari lako."
        },
        "invalid_phone_number": {
            "en": "Please provide a valid phone number.",
            "sw": "Tafadhali toa nambari sahihi ya simu."
        },
        "default": {
            "en": "I'm sorry, I didn't understand that.",
            "sw": "Samahani, sijaelewa."
        }
    }
    return responses.get(key, {}).get(language, responses[key]["en"])  # Default to English if language key is missing


def handle_driver_request(bot_name, user_id, message, response):
    """Handles OTP and transfer requests by checking user input and bot response."""

    # Detect language of user message
    language = detect_language(message)

    # Ensure user_context has an entry for this user
    if user_id not in user_context:
        user_context[user_id] = {}

    # Check if user is requesting OTP
    otp_keywords = ["otp", "sipati"]

    if any(is_match(word, message) for word in otp_keywords):
        phone_number = extract_phone_number(message)
        fleet_number = extract_fleet_number(message)

        # Store extracted values
        if phone_number:
            user_context[user_id]["phone_number"] = phone_number
        if fleet_number:
            user_context[user_id]["fleet_number"] = fleet_number

        # Determine the appropriate response
        if phone_number and fleet_number:
            print(f"Phone number: {phone_number}, Fleet number: {fleet_number}")
            return {bot_name: get_response_text(language, "processing_request")}
        elif phone_number:
            user_context[user_id]["awaiting_fleet_number"] = True
            return {bot_name: get_response_text(language, "awaiting_fleet_number")}
        elif fleet_number:
            user_context[user_id]["awaiting_phone_number"] = True
            return {bot_name: get_response_text(language, "awaiting_phone_number")}
        else:
            user_context[user_id]["awaiting_phone_number"] = True
            user_context[user_id]["awaiting_fleet_number"] = True
            return {bot_name: get_response_text(language, "awaiting_both")}

    # If user needs to provide fleet number
    if user_context.get(user_id, {}).get("awaiting_fleet_number"):
        fleet_number = extract_fleet_number(message)
        if fleet_number:
            user_context[user_id]["fleet_number"] = fleet_number
            user_context[user_id].pop("awaiting_fleet_number")  # Remove flag
            print(f"Fleet number found: {fleet_number}")
            return {bot_name: get_response_text(language, "processing_request")}
        else:
            return {bot_name: get_response_text(language, "invalid_fleet_number")}

    # If user needs to provide phone number
    if user_context.get(user_id, {}).get("awaiting_phone_number"):
        phone_number = extract_phone_number(message)
        if phone_number:
            user_context[user_id]["phone_number"] = phone_number
            user_context[user_id].pop("awaiting_phone_number")  # Remove flag
            print(f"Phone number found: {phone_number}")
            return {bot_name: get_response_text(language, "processing_request")}
        else:
            return {bot_name: get_response_text(language, "invalid_phone_number")}

    # Check for cash transfer requests
    if is_pattern(message, "transfer", "from", "to"):
        match = extract_transfer_details(message)
        if match:
            amount, source_fleet, destination_fleet = match.groups()
            print(f"Transferring ksh {amount} from {source_fleet} to {destination_fleet}")
            return {bot_name: f"Transfer from {source_fleet} to {destination_fleet} initiated. {get_response_text(language, 'processing_request')}"}

    return None  # No special handling needed
