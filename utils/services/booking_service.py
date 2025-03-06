from utils.context import user_context
from lib.logger import Logger

logger = Logger(name="booking_service").get_logger()

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
            "en": "Please provide details of your trip: From <Location A> to <Location B>.",
            "sw": "Tafadhali toa maelezo ya safari yako: Kutoka <Eneo A> hadi <Eneo B>.",
        },
        "processing_request": {
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
            from_index = words.index("from") + 1
            to_index = words.index("to") + 1
            pickup = words[from_index].upper()
            destination = words[to_index].upper()
        except (IndexError, ValueError):
            return {bot_name: get_response_text(language, "booking_info_error")}

    if pickup and destination:
        if pickup in STAGES and destination in STAGES:
            # Log booking details
            logger.info(f"User {user_id} is booking from {pickup} to {destination}")

            # Clear context as request is now processing
            user_context[user_id].pop("awaiting_booking_details", None)

            # Return processing message with extracted details
            stage_info = f"Pickup: {STAGES[pickup]['stage']}\n Route: {STAGES[pickup]['route']}\n Destination: {STAGES[destination]['stage']}."
            return {
                bot_name: f"{get_response_text(language, 'processing_request')} \n\n{stage_info}"
            }
        else:
            return {bot_name: "Sorry, I couldn't find the route. Please try again."}

    return {bot_name: get_response_text(language, "assist_booking")}
