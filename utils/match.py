import re
import translator
from rapidfuzz import fuzz
from langdetect import detect, LangDetectException

from lib.logger import Logger


# Configure logging
logger = Logger(name="otp_request_service").get_logger()


# Function to check for transfer intent
def is_pattern(message, *words, threshold=80):
    """
    Checks if all given words appear in the message in the correct sequence.

    :param message: The user input message
    :param words: Words that should appear in order
    :param threshold: Similarity threshold for fuzzy matching (default: 80)
    :return: True if words appear in order, else False
    """

    message = message.lower()
    pattern = r"\b" + r"\s+".join(re.escape(word) for word in words) + r"\b"

    logger.debug(f"Checking pattern: {pattern} in message: {message}")

    # Check for exact sequence
    if re.search(pattern, message):
        logger.debug("Exact match found!")
        return True

    # Check for fuzzy match in order
    message_words = message.split()
    matched_indices = []

    for word in words:
        for i, msg_word in enumerate(message_words):
            if fuzz.ratio(word.lower(), msg_word) >= threshold:
                matched_indices.append(i)
                break

    result = matched_indices == sorted(matched_indices) and len(matched_indices) == len(
        words
    )
    logger.debug(f"Matched indices: {matched_indices}, Result: {result}")

    return result


# Function to check if a word is in the message with typo tolerance
def is_match(word, message, threshold=80):
    message_words = message.lower().split()
    for msg_word in message_words:
        if fuzz.ratio(word.lower(), msg_word) >= threshold:
            return True
    return False


# Function to detect language every time
def detect_language(message):
    try:
        return detect(message)
    except LangDetectException:
        return "en"  # Default to English if detection fails


def translate_fallback_response(response, target_lang):
    translated_text = translator.translate(response, dest=target_lang).text
    return translated_text


# Function to detect language (default to English if unsure) and store in user context
def detect_and_store_language(user_id, message, user_context):
    if user_id not in user_context:
        user_context[user_id] = {}

    if "language" not in user_context[user_id]:  # Only detect language once
        try:
            language = detect(message)
        except LangDetectException:
            language = "en"  # Default to English if detection fails
        user_context[user_id]["language"] = language

    return user_context[user_id]["language"]
