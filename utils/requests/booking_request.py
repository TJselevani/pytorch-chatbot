from utils.context import user_context
from utils.match import detect_language
from utils.handlers.booking_handler import (
    handle_booking_request,
    handle_awaiting_booking_confirmation,
)
from utils.match import is_match, is_pattern

from lib.logger import Logger

# Configure logging - create only one instance
logger = Logger(name="booking_requests", separate_file=True).get_logger()


def get_booking(bot_name, user_id, message):
    """Handles passenger inquiries before running intent classification."""

    # Detect message language
    language = detect_language(message)

    # Ensure user_context has an entry for this user
    if user_id not in user_context:
        user_context[user_id] = {}

    # First, try to handle awaiting booking details states
    if user_context[user_id].get("awaiting_booking_confirmation"):
        otp_response = handle_awaiting_booking_confirmation(
            bot_name, user_id, message, language
        )
        if otp_response:
            logger.debug(f"Handled awaiting OTP details: {otp_response}")
            return otp_response

    # {1} Process booking requests
    booking_keywords = ["reserve", "save", "nafasi", "book"]
    if (
        any(is_match(word, message) for word in booking_keywords)
        or is_pattern(message, "reserve", "from", "to")
        or is_pattern(message, "save", "from", "to")
        or is_pattern(message, "book", "from", "to")
        or is_pattern(message, "nafasi", "kutoka", "hadi")
    ):
        logger.info("Booking request detected")
        response = handle_booking_request(bot_name, user_id, message, language)
        if response:
            return response

    return None  # Return None if no special handling is needed
