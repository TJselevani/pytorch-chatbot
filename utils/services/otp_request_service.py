import os
import sys
from utils.context import user_context
from utils.extractors import (
    extract_phone_number,
    extract_fleet_number,
    extract_transfer_details,
)
from utils.match import is_match, is_pattern, detect_language
from lib.logger import Logger

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
        logger.debug(
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
    # Check if we're in a state of awaiting both phone and fleet number
    if user_context.get(user_id, {}).get("awaiting_fleet_and_phone"):
        # First, try to extract fleet number
        if not user_context[user_id].get("fleet_number"):
            fleet_number = extract_fleet_number(message)
            if fleet_number:
                user_context[user_id]["fleet_number"] = fleet_number
                logger.debug(f"Fleet number found in awaiting state: {fleet_number}")

                # If we already have a phone number, proceed
                if user_context[user_id].get("phone_number"):
                    user_context[user_id].pop("awaiting_fleet_and_phone", None)
                    bot_response = {
                        bot_name: get_response_text(language, "processing_request")
                    }
                    logger.debug(
                        f"Both phone and fleet number received. Bot Response: {bot_response}"
                    )
                    return bot_response

                # Otherwise, continue awaiting phone number
                bot_response = {
                    bot_name: get_response_text(language, "awaiting_phone_number")
                }
                logger.debug(f"Awaiting Phone Number. Bot Response: {bot_response}")
                return bot_response

        # Then, try to extract phone number
        if not user_context[user_id].get("phone_number"):
            phone_number = extract_phone_number(message)
            if phone_number:
                user_context[user_id]["phone_number"] = phone_number
                logger.debug(f"Phone number found in awaiting state: {phone_number}")

                # If we already have a fleet number, proceed
                if user_context[user_id].get("fleet_number"):
                    user_context[user_id].pop("awaiting_fleet_and_phone", None)
                    bot_response = {
                        bot_name: get_response_text(language, "processing_request")
                    }
                    logger.debug(
                        f"Both phone and fleet number received. Bot Response: {bot_response}"
                    )
                    return bot_response

                # Otherwise, continue awaiting fleet number
                bot_response = {
                    bot_name: get_response_text(language, "awaiting_fleet_number")
                }
                logger.debug(f"Awaiting Fleet Number. Bot Response: {bot_response}")
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
