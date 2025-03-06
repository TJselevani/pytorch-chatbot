import re
from utils.context import user_context
from utils.match import detect_language
from utils.services.booking_service import handle_booking_request
from utils.services.payment_service import (
    handle_awaiting_transfer_confirmation,
    handle_transfer_request,
)
from utils.services.wallet_service import handle_wallet_queries
from utils.match import is_match, is_pattern

from lib.logger import Logger

# Configure logging - create only one instance
logger = Logger(name="passenger_requests").get_logger()


def handle_passenger_request(bot_name, user_id, message, response):
    """Handles passenger inquiries before running intent classification."""
    # Detect message language
    language = detect_language(message)

    # Ensure user_context has an entry for this user
    if user_id not in user_context:
        user_context[user_id] = {}

    # Check for transfer confirmation
    await_transfer_response = handle_awaiting_transfer_confirmation(
        bot_name, user_id, message, language
    )
    if await_transfer_response:
        logger.debug(
            f"Handled awaiting transfer confirmation: {await_transfer_response}"
        )
        return await_transfer_response

    # {1} Process booking requests
    booking_keywords = ["reserve", "save", "nafasi"]
    if (
        any(is_match(word, message) for word in booking_keywords)
        or is_pattern(message, "reserve", "from", "to")
        or is_pattern(message, "save", "from", "to")
        or is_pattern(message, "nafasi", "kutoka", "hadi")
    ):
        response = handle_booking_request(bot_name, user_id, message, language)
        if response:
            return response

    # {2} Process wrong payment corrections
    wrong_payment_keywords = ["wrong fleet", "incorrect fleet", "transfer"]
    if any(is_match(word, message) for word in wrong_payment_keywords):
        if is_pattern(message, "transfer", "from", "to") or re.search(
            r"\d+(?:\.\d{2})?\s+(se|sm)\d{2}\s+(se|sm)\d{2}", message, re.IGNORECASE
        ):
            logger.debug("Transfer request detected")
            return handle_transfer_request(bot_name, user_id, message, language)

    # {3} Process wallet-related queries
    response = handle_wallet_queries(bot_name, message, language)
    if response:
        return response

    return None  # Return None if no special handling is needed
