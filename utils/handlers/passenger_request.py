import os
import sys
from utils.context import user_context
from utils.extractors import extract_fleet_number, extract_transfer_details
from utils.match import is_match, detect_language

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Function to get the response in the detected language
def get_response_text(language, key):
    responses = {
        "booking_info": {
            "en": "You can book a vehicle using our app. Let me know if you need further assistance!",
            "sw": "Unaweza kuweka nafasi ya gari kwa kutumia programu yetu. Nijulishe ikiwa unahitaji msaada zaidi!"
        },
        "assist_booking": {
            "en": "Please provide details of your trip: From <Location A> to <Location B>.",
            "sw": "Tafadhali toa maelezo ya safari yako: Kutoka <Eneo A> hadi <Eneo B>."
        },
        "transfer_request": {
            "en": "Please share your fleet number in this format: from <se00> to <se01>.",
            "sw": "Tafadhali shiriki nambari yako ya gari kwa fomati hii: kutoka <se00> hadi <se01>."
        },
        "processing_request": {
            "en": "Please wait as we process your request.",
            "sw": "Tafadhali subiri tunashughulikia ombi lako."
        },
        "wallet_info": {
            "en": "You can load your wallet using mobile money or bank transfer. Let me know if you need help!",
            "sw": "Unaweza kuweka pesa kwenye pochi yako kwa kutumia pesa za simu au uhamisho wa benki. Nijulishe ikiwa unahitaji msaada!"
        },
        "wallet_payment": {
            "en": "To pay from your wallet, select 'Wallet' as your payment method in the app.",
            "sw": "Ili kulipa kutoka kwenye pochi yako, chagua 'Pochi' kama njia yako ya malipo kwenye programu."
        },
        "default": {
            "en": "I'm sorry, I didn't understand that.",
            "sw": "Samahani, sijaelewa."
        }
    }
    return responses.get(key, {}).get(language, responses[key]["en"])  # Default to English if language key is missing


def handle_passenger_request(bot_name, user_id, message):
    """Handles passenger inquiries before running intent classification."""
    # Detect message language
    language = detect_language(user_id, message, user_context)

    # Ensure user_context has an entry for this user
    if user_id not in user_context:
        user_context[user_id] = {}
    
    # Booking related queries
    booking_keywords = ["book", "naeza book"]
    if any(is_match(word, message) for word in booking_keywords):
        return {bot_name: get_response_text(language, "booking_info")}
    
    if "help me book" in message.lower():
        return {bot_name: get_response_text(language, "assist_booking")}
    
    # Transfer request
    if "wrong fleet number" in message.lower():
        user_context[user_id]["awaiting_fleet_number"] = True
        return {bot_name: get_response_text(language, "transfer_request")}
    
    if user_context.get(user_id, {}).get("awaiting_fleet_number"):
        fleet_number = extract_fleet_number(message)
        if fleet_number:
            user_context[user_id].pop("awaiting_fleet_number")  # Clear flag
            return {bot_name: get_response_text(language, "processing_request")}
        else:
            return {bot_name: get_response_text(language, "transfer_request")}
    
    # Wallet-related queries
    if "load my wallet" in message.lower():
        return {bot_name: get_response_text(language, "wallet_info")}
    
    if "pay from my wallet" in message.lower():
        return {bot_name: get_response_text(language, "wallet_payment")}
    
    return None  # Return None if no special handling is needed
