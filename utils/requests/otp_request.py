from utils.context import user_context
from utils.handlers.otp_handler import (
    handle_awaiting_otp_details,
    handle_get_otp_request,
)
from utils.match import is_match, detect_language
from lib.logger import Logger

# Configure logging - create only one instance
logger = Logger(name="get_otp_requests", separate_file=True).get_logger()


def get_otp(bot_name, user_id, message):
    """Handles OTP and transfer requests by checking user input and bot response."""

    # Detect language of user message
    language = detect_language(message)

    # Ensure user_context has an entry for this user
    if user_id not in user_context:
        user_context[user_id] = {}

    # First, try to handle awaiting OTP details states
    if user_context[user_id].get("awaiting_otp_request"):
        otp_response = handle_awaiting_otp_details(bot_name, user_id, message, language)
        if otp_response:
            logger.debug(f"Handled awaiting OTP details: {otp_response}")
            return otp_response

    # {1} Check if user is requesting OTP
    otp_keywords = ["otp", "code"]
    if any(is_match(word, message) for word in otp_keywords):
        logger.info("OTP request detected")

        # Set conversation state for expecting OTP input
        user_context[user_id]["awaiting_otp_request"] = True

        # Trigger OTP request function
        return handle_get_otp_request(bot_name, user_id, message, language)

    # For non-specific interactions after successful processing, reset awaiting flags
    if user_context.get(user_id, {}).get("phone_number") and user_context.get(
        user_id, {}
    ).get("fleet_number"):
        # Clear any awaiting flags if both phone and fleet numbers are present
        user_context[user_id].pop("awaiting_phone_number", None)
        user_context[user_id].pop("awaiting_fleet_number", None)
        user_context[user_id].pop("awaiting_fleet_and_phone", None)

    logger.debug("No special handling needed")
    return None  # No special handling needed
