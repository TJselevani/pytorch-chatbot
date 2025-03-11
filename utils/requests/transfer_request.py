from utils.context import user_context
from utils.handlers.payment_handler import (
    handle_transfer_request,
    handle_awaiting_transfer_confirmation,
)
from utils.match import is_match, is_pattern, detect_language
from lib.logger import Logger

# Configure logging - create only one instance
logger = Logger(name="transfer_requests", separate_file=True).get_logger()


def transfer_payment(bot_name, user_id, message):
    """Handles OTP and transfer requests by checking user input and bot response."""

    # Detect language of user message
    language = detect_language(message)

    # Ensure user_context has an entry for this user
    if user_id not in user_context:
        user_context[user_id] = {}

    # First Check for previous transfer intent confirmation
    if user_context[user_id].get("awaiting_transfer_request"):
        transfer_response = handle_awaiting_transfer_confirmation(
            bot_name, user_id, message, language
        )
        if transfer_response:
            logger.debug(f"Handled awaiting transfer confirmation: {transfer_response}")
            return transfer_response

    # {1} Check for cash transfer requests - use is_pattern to detect transfer patterns
    transfer_key_words = [
        "transfer",
        "send money",
        "move funds",
        "shift balance",
        "money to",
    ]

    if any(is_match(word, message) for word in transfer_key_words):
        if is_pattern(message, "transfer", "from", "to"):
            logger.info("Transfer request detected")
            return handle_transfer_request(bot_name, user_id, message, language)

    logger.debug("No special handling needed")
    return None  # No special handling needed
