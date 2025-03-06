import os
import re
import sys
from utils.context import user_context
from utils.extractors import extract_phone_number, extract_fleet_number
from utils.services.otp_request_service import (
    handle_awaiting_otp_details,
    handle_otp_request,
)
from utils.services.transfer_request_service import (
    handle_transfer_request,
    handle_awaiting_transfer_confirmation,
)
from utils.match import is_match, is_pattern, detect_language
from lib.logger import Logger

# Configure logging - create only one instance
logger = Logger(name="driver_requests").get_logger()


def handle_driver_request(bot_name, user_id, message, response):
    """Handles OTP and transfer requests by checking user input and bot response."""

    # Log the initial message and bot response
    logger.debug(f"User ID: {user_id}")
    logger.debug(f"Received Message: {message}")
    logger.debug(f"Bot Response: {response}")

    # Detect language of user message
    language = detect_language(message)

    # Ensure user_context has an entry for this user
    if user_id not in user_context:
        user_context[user_id] = {}

    # First, try to handle awaiting details states
    await_otp_response = handle_awaiting_otp_details(
        bot_name, user_id, message, language
    )
    if await_otp_response:
        logger.debug(f"Handled awaiting OTP details: {await_otp_response}")
        return await_otp_response

    # Check for transfer confirmation
    await_transfer_response = handle_awaiting_transfer_confirmation(
        bot_name, user_id, message, language
    )
    if await_transfer_response:
        logger.debug(
            f"Handled awaiting transfer confirmation: {await_transfer_response}"
        )
        return await_transfer_response

    # {1} Check if user is requesting OTP
    otp_keywords = ["otp", "code"]
    if any(is_match(word, message) for word in otp_keywords):
        logger.debug("OTP request detected")
        return handle_otp_request(bot_name, user_id, message, language)

    # {2} Check for cash transfer requests - use is_pattern to detect transfer patterns
    transfer_key_words = ["transfer", "from", "to"]
    if any(is_match(word, message) for word in transfer_key_words):
        if is_pattern(message, "transfer", "from", "to") or re.search(
            r"\d+(?:\.\d{2})?\s+(se|sm)\d{2}\s+(se|sm)\d{2}", message, re.IGNORECASE
        ):
            logger.debug("Transfer request detected")
            return handle_transfer_request(bot_name, user_id, message, language)

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
