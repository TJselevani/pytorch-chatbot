from utils.context import user_context
from utils.match import detect_language
from utils.handlers.payment_handler import (
    handle_awaiting_recover_confirmation,
    handle_recover_request,
)
from utils.match import is_match, is_pattern

from lib.logger import Logger

# Configure logging - create only one instance
logger = Logger(name="recover_requests", separate_file=True).get_logger()


def recover_payment(bot_name, user_id, message):
    """Handles passenger inquiries before running intent classification."""

    # Detect message language
    language = detect_language(message)

    # Ensure user_context has an entry for this user
    if user_id not in user_context:
        user_context[user_id] = {}

    # Check for awaiting transfer confirmation
    if user_context[user_id].get("awaiting_recover_request"):
        recover_response = handle_awaiting_recover_confirmation(
            bot_name, user_id, message, language
        )
        if recover_response:
            logger.debug(f"Handled awaiting recover confirmation: {recover_response}")
            return recover_response

    # {1} Process wrong payment corrections
    wrong_payment_keywords = ["recover", "wrong fleet", "incorrect fleet", "mistake"]
    if any(is_match(word, message) for word in wrong_payment_keywords):
        if is_pattern(message, "recover", "from", "to"):
            logger.info("Recover request detected")
            return handle_recover_request(bot_name, user_id, message, language)

    logger.debug("No special handling needed")
    return None  # Return None if no special handling is needed
