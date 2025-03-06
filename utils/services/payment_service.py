import re
from utils.context import user_context
from lib.logger import Logger

# Configure logging - only create one instance
logger = Logger(name="transfer_request_service").get_logger()


def get_response_text(language, key):
    responses = {
        "awaiting_transfer_confirmation": {
            "en": "Please confirm the transfer by replying with 'yes'.",
            "sw": "Tafadhali thibitisha uhamisho kwa kujibu 'ndio'.",
        },
        "processing_request": {
            "en": "Kindly wait as your request is being processed.",
            "sw": "Tafadhali subiri ombi lako linashughulikiwa.",
        },
        "invalid_transfer_details": {
            "en": "Please provide a valid amount and fleet numbers.",
            "sw": "Tafadhali toa kiasi halali na nambari za gari.",
        },
        "default": {
            "en": "I'm sorry, I didn't understand that.",
            "sw": "Samahani, sijaelewa.",
        },
    }
    return responses.get(key, {}).get(language, responses[key]["en"])


def extract_transfer_details(message):
    """Extract amount and fleet numbers from a transfer message."""

    # Updated pattern to allow "ksh", "KES", "from", and "to"
    pattern = r"(?:ksh|KES)?\s*(?P<amount>\d+(?:\.\d{2})?)\s*(?:from)?\s*(?P<source_fleet>(se|sm)\d{2})\s*(?:to)?\s*(?P<destination_fleet>(se|sm)\d{2})"

    match = re.search(pattern, message, re.IGNORECASE)

    if match:
        amount = match.group("amount")
        source_fleet = match.group("source_fleet")
        destination_fleet = match.group("destination_fleet")

        logger.debug(
            f"Extracted: amount={amount}, source={source_fleet}, dest={destination_fleet}"
        )
        return amount, source_fleet, destination_fleet

    logger.debug(f"No transfer details found in message: {message}")
    return None


def handle_transfer_request(bot_name, user_id, message, language):
    """Handle cash transfer request processing."""
    logger.debug("Processing transfer request")

    # Extract transfer details directly
    details = extract_transfer_details(message)
    logger.debug(f"After extraction: {details}")

    if details:
        amount, source_fleet, destination_fleet = details

        # Store transfer details in user context
        if user_id not in user_context:
            user_context[user_id] = {}

        user_context[user_id]["pending_transfer"] = {
            "amount": amount,
            "source_fleet": source_fleet,
            "destination_fleet": destination_fleet,
        }
        user_context[user_id]["awaiting_transfer_confirmation"] = True

        response_text = get_response_text(language, "awaiting_transfer_confirmation")
        logger.debug(f"Set awaiting confirmation. Response: {response_text}")
        return {bot_name: response_text}

    logger.debug("Invalid transfer details, sending error response")
    return {bot_name: get_response_text(language, "invalid_transfer_details")}


def handle_awaiting_transfer_confirmation(bot_name, user_id, message, language):
    """Handle user confirmation for transfer."""
    # logger.debug(f"Checking for pending transfer for user {user_id}")

    # First check if this user has a pending transfer
    if user_id in user_context and user_context[user_id].get(
        "awaiting_transfer_confirmation"
    ):
        # Check for confirmation in either language
        confirmation_msg = message.strip().lower()
        logger.debug(f"Got confirmation message: '{confirmation_msg}'")

        if confirmation_msg in ["yes", "ndio"]:
            # Get transfer details
            transfer_details = user_context[user_id].get("pending_transfer", {})

            # Clean up context
            user_context[user_id].pop("pending_transfer", None)
            user_context[user_id].pop("awaiting_transfer_confirmation", None)

            # Log the confirmed transfer
            amount = transfer_details.get("amount")
            source = transfer_details.get("source_fleet")
            destination = transfer_details.get("destination_fleet")
            logger.info(f"Transfer confirmed: {amount} from {source} to {destination}")

            # Send processing response
            return {bot_name: get_response_text(language, "processing_request")}

    # No pending transfer or confirmation not recognized
    # logger.debug("No confirmation needed or not recognized")
    return None
