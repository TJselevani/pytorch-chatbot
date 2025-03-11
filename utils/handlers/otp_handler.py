import time
from utils.context import user_context
from utils.extractors import (
    extract_phone_number,
    extract_fleet_number,
)
from lib.logger import Logger
from utils.services.account_service import AccountService
from config import SMS_CONFIG

TIMEOUT_SECONDS = 180  # 1-minute timeout

# Configure logging
logger = Logger(name="otp_handler", separate_file=True).get_logger()

# Initialize AccountService with API details
SMS_API_KEY = SMS_CONFIG["apiKey"]
SMS_BASE_URL = SMS_CONFIG["baseurl"]  # "YOUR_SMS_API_URL"
SENDER_ID = SMS_CONFIG["senderID"]
account_service = AccountService(SMS_API_KEY, SMS_BASE_URL, SENDER_ID)


# Function to get the response in the detected language
def get_response_text(language, key):
    responses = {
        "awaiting_fleet_number": {
            "en": "Okay, kindly help me with your fleet number.",
            "sw": "Sawa, tafadhali nisaidie na nambari ya gari lako.",
        },
        "invalid_fleet_number": {
            "en": "Please provide a valid fleet number.",
            "sw": "Tafadhali nisaidie nambari sahihi ya gari lako.",
        },
        "awaiting_phone_number": {
            "en": "Kindly provide your phone number.",
            "sw": "Tafadhali toa nambari yako ya simu.",
        },
        "invalid_phone_number": {
            "en": "Please provide a valid phone number.",
            "sw": "Tafadhali toa nambari sahihi ya simu.",
        },
        "awaiting_both": {
            "en": "Please provide both your phone number and fleet number.",
            "sw": "Tafadhali toa nambari yako ya simu na nambari ya gari lako.",
        },
        "processing_request": {
            "en": "Kindly wait as your request is being processed.",
            "sw": "Tafadhali subiri ombi lako linashughulikiwa.",
        },
        "otp_sent_success": {
            "en": "An OTP has been sent to your phone number. Please enter it to proceed.",
            "sw": "OTP imetumwa kwa nambari yako ya simu. Tafadhali ingiza ili kuendelea.",
        },
        "otp_failed": {
            "en": "Failed to send OTP. Please try again later.",
            "sw": "Imeshindikana kutuma OTP. Tafadhali jaribu tena baadaye.",
        },
        "default": {
            "en": "I'm sorry, I didn't understand that.",
            "sw": "Samahani, sijaelewa.",
        },
    }
    return responses.get(key, {}).get(
        language, responses[key]["en"]
    )  # Default to English if language key is missing


def handle_get_otp_request(bot_name, user_id, message, language):
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
        user_context[user_id]["awaiting_otp_verification"] = True
        logger.info(f"Sending OTP to {phone_number} for Fleet {fleet_number}")
        otp_response = account_service.send_otp(phone_number)

        if otp_response.get("status") == "success":
            bot_response = {bot_name: get_response_text(language, "otp_sent_success")}
            logger.info("OTP sent successfully.")
        else:
            bot_response = {bot_name: get_response_text(language, "otp_failed")}
            logger.error(f"Failed to send OTP: {otp_response.get('details', '')}")

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
        user_context.pop(user_id, None)
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
            # Clear the awaiting state once OTP is processed
            user_context[user_id].pop("awaiting_otp_request", None)
            logger.info(f"Both details received. Bot Response: {bot_response}")

            user_context[user_id]["awaiting_otp_verification"] = True
            logger.info(f"Sending OTP to {phone_number} for Fleet {fleet_number}")
            otp_response = account_service.send_otp(phone_number)

            if otp_response.get("status") == "success":
                bot_response = {
                    bot_name: get_response_text(language, "otp_sent_success")
                }
                logger.info("OTP sent successfully.")
            else:
                bot_response = {bot_name: get_response_text(language, "otp_failed")}
                logger.error(f"Failed to send OTP: {otp_response.get('details', '')}")
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

            # Clear the awaiting state once OTP is processed
            user_context[user_id].pop("awaiting_otp_request", None)
            bot_response = {bot_name: get_response_text(language, "processing_request")}

            user_context[user_id]["awaiting_otp_verification"] = True
            logger.info(f"Sending OTP to {phone_number} for Fleet {fleet_number}")
            otp_response = account_service.send_otp(phone_number)

            if otp_response.get("status") == "success":
                bot_response = {
                    bot_name: get_response_text(language, "otp_sent_success")
                }
                logger.info("OTP sent successfully.")
            else:
                bot_response = {bot_name: get_response_text(language, "otp_failed")}
                logger.error(f"Failed to send OTP: {otp_response.get('details', '')}")
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

            # Clear the awaiting state once OTP is processed
            user_context[user_id].pop("awaiting_otp_request", None)
            bot_response = {bot_name: get_response_text(language, "processing_request")}

            user_context[user_id]["awaiting_otp_verification"] = True
            logger.info(f"Sending OTP to {phone_number} for Fleet {fleet_number}")
            otp_response = account_service.send_otp(phone_number)

            if otp_response.get("status") == "success":
                bot_response = {
                    bot_name: get_response_text(language, "otp_sent_success")
                }
                logger.info("OTP sent successfully.")
            else:
                bot_response = {bot_name: get_response_text(language, "otp_failed")}
                logger.error(f"Failed to send OTP: {otp_response.get('details', '')}")
            logger.debug(f"Bot Response: {bot_response}")
            return bot_response
        else:
            bot_response = {
                bot_name: get_response_text(language, "invalid_phone_number")
            }
            logger.debug(f"Bot Response: {bot_response}")
            return bot_response

    return None


def handle_verify_otp(bot_name, user_id, message, language):
    """Handles OTP verification after the user enters the received OTP."""
    phone_number = user_context.get(user_id, {}).get("phone_number")

    if not phone_number:
        logger.error(f"No phone number found for user {user_id}")
        user_context.pop(user_id, None)  # Clear stored context
        return {bot_name: "Your OTP session has expired. Please request a new OTP."}

    user_otp = message.strip()

    otp_response = account_service.verify_otp(phone_number, user_otp)

    if otp_response["status"] == "success":
        logger.info(f"User {user_id} successfully verified OTP.")
        user_context.pop(user_id, None)  # Clear stored context after success
        return {bot_name: otp_response["message"]}
    else:
        logger.warning(f"User {user_id} entered an incorrect or expired OTP.")
        return {bot_name: otp_response["message"]}

    return None
