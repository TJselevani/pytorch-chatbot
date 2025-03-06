import time
from utils.context import user_context
from utils.extractors import (
    extract_phone_number,
    extract_fleet_number,
)
from lib.logger import Logger

TIMEOUT_SECONDS = 60  # 1-minute timeout

# Configure logging
logger = Logger(name="otp_request_service").get_logger()


# Function to get the response in the detected language
def get_response_text(language, key):
    responses = {
        "awaiting_fleet_number": {
            "en": "Okay, kindly help me with your fleet number.",
            "sw": "Sawa, tafadhali nisaidie na nambari ya gari lako.",
        },
        "awaiting_phone_number": {
            "en": "Kindly provide your phone number.",
            "sw": "Tafadhali toa nambari yako ya simu.",
        },
        "awaiting_both": {
            "en": "Please provide both your phone number and fleet number.",
            "sw": "Tafadhali toa nambari yako ya simu na nambari ya gari lako.",
        },
        "processing_request": {
            "en": "Kindly wait as your request is being processed.",
            "sw": "Tafadhali subiri ombi lako linashughulikiwa.",
        },
        "invalid_fleet_number": {
            "en": "Please provide a valid fleet number.",
            "sw": "Tafadhali nisaidie nambari sahihi ya gari lako.",
        },
        "invalid_phone_number": {
            "en": "Please provide a valid phone number.",
            "sw": "Tafadhali toa nambari sahihi ya simu.",
        },
        "default": {
            "en": "I'm sorry, I didn't understand that.",
            "sw": "Samahani, sijaelewa.",
        },
    }
    return responses.get(key, {}).get(
        language, responses[key]["en"]
    )  # Default to English if language key is missing


def handle_otp_request(bot_name, user_id, message, language):
    """Handle OTP request processing."""
    logger.debug("Processing OTP request")

    # Extract phone number and fleet number if available
    phone_number = extract_phone_number(message)
    fleet_number = extract_fleet_number(message)

    # Log extraction results
    if phone_number:
        logger.debug(f"Phone number found: {phone_number}")
        user_context[user_id]["phone_number"] = phone_number

    if fleet_number:
        logger.debug(f"Fleet number found: {fleet_number}")
        user_context[user_id]["fleet_number"] = fleet_number

    # Check if both phone and fleet numbers are available
    phone_number = user_context.get(user_id, {}).get("phone_number")
    fleet_number = user_context.get(user_id, {}).get("fleet_number")

    if phone_number and fleet_number:
        logger.info(
            f"Processing OTP request with Phone number: {phone_number}, Fleet number: {fleet_number}"
        )
        bot_response = {bot_name: get_response_text(language, "processing_request")}
        logger.debug(f"Bot Response: {bot_response}")
        return bot_response
    else:
        # Set state to awaiting both phone and fleet number
        user_context[user_id]["awaiting_fleet_and_phone"] = True
        bot_response = {bot_name: get_response_text(language, "awaiting_both")}
        logger.debug("Awaiting both Phone Number and Fleet Number")
        logger.debug(f"Bot Response: {bot_response}")
        return bot_response


def handle_awaiting_otp_details(bot_name, user_id, message, language):
    """Handle processing when awaiting user details."""
    current_time = time.time()
    user_state = user_context.get(user_id, {})

    # Check if the request has timed out
    request_start_time = user_state.get("request_start_time")
    if request_start_time and (current_time - request_start_time > TIMEOUT_SECONDS):
        # Clear the user context since the request expired
        user_context[user_id] = {}
        logger.debug(f"Request timed out for user {user_id}. Context cleared.")

        return {bot_name: get_response_text(language, "request_timed_out")}

    # If we're just now awaiting details, store the request start time
    if (
        "awaiting_fleet_and_phone" in user_state
        and "request_start_time" not in user_state
    ):
        user_context[user_id]["request_start_time"] = current_time

    awaiting_fleet_and_phone = user_state.get("awaiting_fleet_and_phone", False)
    fleet_number = user_state.get("fleet_number")
    phone_number = user_state.get("phone_number")

    # If awaiting both details, attempt to extract both at once
    if awaiting_fleet_and_phone:
        if not fleet_number:
            fleet_number = extract_fleet_number(message)
            if fleet_number:
                user_context[user_id]["fleet_number"] = fleet_number
                logger.debug(f"Extracted fleet number: {fleet_number}")

        if not phone_number:
            phone_number = extract_phone_number(message)
            if phone_number:
                user_context[user_id]["phone_number"] = phone_number
                logger.debug(f"Extracted phone number: {phone_number}")

        # Check if we have both details now
        if fleet_number and phone_number:
            user_context[user_id].pop("awaiting_fleet_and_phone", None)
            bot_response = {bot_name: get_response_text(language, "processing_request")}
            logger.info(f"Both details received. Bot Response: {bot_response}")
            return bot_response

        # If still missing details, prompt for the missing one
        if not fleet_number:
            bot_response = {
                bot_name: get_response_text(language, "awaiting_fleet_number")
            }
            logger.info("Awaiting Fleet Number.")
            return bot_response

        if not phone_number:
            bot_response = {
                bot_name: get_response_text(language, "awaiting_phone_number")
            }
            logger.info("Awaiting Phone Number.")
            return bot_response

    # If user needs to provide fleet number
    if user_context.get(user_id, {}).get("awaiting_fleet_number"):
        fleet_number = extract_fleet_number(message)
        if fleet_number:
            user_context[user_id]["fleet_number"] = fleet_number
            user_context[user_id].pop("awaiting_fleet_number")  # Remove flag
            logger.debug(f"Fleet number found: {fleet_number}")

            # Log existing phone number if available
            existing_phone = user_context.get(user_id, {}).get("phone_number")
            if existing_phone:
                logger.debug(f"Existing Phone number: {existing_phone}")

            bot_response = {bot_name: get_response_text(language, "processing_request")}
            logger.debug(f"Bot Response: {bot_response}")
            return bot_response
        else:
            bot_response = {
                bot_name: get_response_text(language, "invalid_fleet_number")
            }
            logger.debug(f"Bot Response: {bot_response}")
            return bot_response

    # If user needs to provide phone number
    if user_context.get(user_id, {}).get("awaiting_phone_number"):
        phone_number = extract_phone_number(message)
        if phone_number:
            user_context[user_id]["phone_number"] = phone_number
            user_context[user_id].pop("awaiting_phone_number")  # Remove flag
            logger.debug(f"Phone number found: {phone_number}")

            # Log existing fleet number if available
            existing_fleet = user_context.get(user_id, {}).get("fleet_number")
            if existing_fleet:
                logger.debug(f"Existing Fleet number: {existing_fleet}")

            bot_response = {bot_name: get_response_text(language, "processing_request")}
            logger.debug(f"Bot Response: {bot_response}")
            return bot_response
        else:
            bot_response = {
                bot_name: get_response_text(language, "invalid_phone_number")
            }
            logger.debug(f"Bot Response: {bot_response}")
            return bot_response

    return None
