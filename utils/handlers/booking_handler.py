from utils.context import user_context
from lib.logger import Logger

logger = Logger(name="booking_handler", separate_file=True).get_logger()

# Dummy data for vehicle routes
STAGES = {
    "A": {"stage": "Main Terminal", "route": "Route 1 - A to B Express"},
    "B": {"stage": "West Junction", "route": "Route 1 - A to B Express"},
    "C": {"stage": "East Market", "route": "Route 2 - A to C Loop"},
}


# Function to get the response in the detected language
def get_response_text(language, key):
    responses = {
        "booking_info": {
            "en": "You can book a vehicle using our app. Let me know if you need further assistance!",
            "sw": "Unaweza kuweka nafasi ya gari kwa kutumia programu yetu. Nijulishe ikiwa unahitaji msaada zaidi!",
        },
        "booking_info_error": {
            "en": "Please specify both pickup and destination locations correctly.",
            "sw": "Unaweza kuweka nafasi ya gari kwa kutumia programu yetu. Nijulishe ikiwa unahitaji msaada zaidi!",
        },
        "assist_booking": {
            "en": "Please provide details of your trip: Book from <Location A> to <Location B>.",
            "sw": "Tafadhali toa maelezo ya safari yako: Nafasi Kutoka <Eneo A> hadi <Eneo B>.",
        },
        "processing_request": {
            "en": "Type 'Yes' to confirm booking request",
            "sw": "Kamilisha ombi lako kwa kutuma neno 'Yes' au 'ndio'",
        },
        "processing": {
            "en": "Please wait as we process your request.",
            "sw": "Tafadhali subiri tunashughulikia ombi lako.",
        },
        "default": {
            "en": "I'm sorry, I didn't understand that.",
            "sw": "Samahani, sijaelewa.",
        },
    }
    return responses.get(key, {}).get(
        language, responses[key]["en"]
    )  # Default to English if missing


def handle_booking_request(bot_name, user_id, message, language):
    """Handles booking-related queries by extracting trip details, logging them, and responding."""

    # Mark user as awaiting booking details
    user_context[user_id]["awaiting_booking_details"] = True

    words = message.lower().split()
    pickup, destination = None, None

    # Extract pickup and destination if the message contains "from" and "to"
    if "from" in words and "to" in words:
        try:
            from_index = words.index("from" or "kutoka") + 1
            to_index = words.index("to" or "hadi") + 1
            pickup = words[from_index].upper()
            destination = words[to_index].upper()
        except (IndexError, ValueError):
            return {bot_name: get_response_text(language, "booking_info_error")}

    if pickup and destination:
        if pickup in STAGES and destination in STAGES:
            # Log booking details
            logger.info(f"User {user_id} is booking from {pickup} to {destination}")

            # Clear context as request is now processing
            user_context[user_id]["awaiting_booking_confirmation"] = True

            # Return processing message with extracted details
            stage_info = f"Pickup: {STAGES[pickup]['stage']}\n Route: {STAGES[pickup]['route']}\n Destination: {STAGES[destination]['stage']}."
            return {
                bot_name: f"{get_response_text(language, 'processing_request')} \n\n{stage_info}"
            }
        else:
            return {bot_name: "Sorry, I couldn't find the route. Please try again."}

    return {bot_name: get_response_text(language, "assist_booking")}


def handle_awaiting_booking_confirmation(bot_name, user_id, message, language):
    """Confirms user's booking request"""

    # First check if this user has a pending booking request
    if user_id in user_context and user_context[user_id].get(
        "awaiting_booking_confirmation"
    ):
        # Check for confirmation in either language
        confirmation_msg = message.strip().lower()
        logger.debug(f"Got confirmation message: '{confirmation_msg}'")

        if confirmation_msg in ["yes", "ndio"]:
            # Get transfer details
            booking_details = user_context[user_id].get("pending_transfer", {})

            # Clean up context
            user_context[user_id].pop("pending_transfer", None)
            user_context[user_id].pop("awaiting_transfer_confirmation", None)

            # Log the confirmed transfer
            amount = booking_details.get("amount")
            source = booking_details.get("source_fleet")
            destination = booking_details.get("destination_fleet")
            logger.info(f"Transfer confirmed: {amount} from {source} to {destination}")

            user_context[user_id].pop("awaiting_booking_confirmation", None)

            # Send processing response
            return {bot_name: get_response_text(language, "processing")}

    return None
