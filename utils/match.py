import re
from rapidfuzz import fuzz
from langdetect import detect

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
    pattern = r'\b' + r'\s+'.join(re.escape(word) for word in words) + r'\b'
    
    # Check for exact sequence
    if re.search(pattern, message):
        return True

    # Check for fuzzy match in order
    message_words = message.split()
    matched_indices = []
    
    for word in words:
        for i, msg_word in enumerate(message_words):
            if fuzz.ratio(word.lower(), msg_word) >= threshold:
                matched_indices.append(i)
                break

    return matched_indices == sorted(matched_indices) and len(matched_indices) == len(words)


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
    except:
        return "en"  # Default to English if detection fails

# Detect language from stored intents
def detect_language_from_patterns(message, intents_data):
    """Manually detect language based on known patterns in Swahili or English."""
    message_lower = message.lower()

    sw_patterns = []
    en_patterns = []

    for intent in intents_data["intents"]:
        sw_patterns.extend(intent.get("patterns", {}).get("sw", []))
        en_patterns.extend(intent.get("patterns", {}).get("en", []))

    print(f"Checking '{message}' against: \nSwahili: {sw_patterns}\nEnglish: {en_patterns}")

    if any(pattern.lower() in message_lower for pattern in sw_patterns):
        return "sw"
    elif any(pattern.lower() in message_lower for pattern in en_patterns):
        return "en"

    return "en"

# Function to detect language (default to English if unsure) and store in user context
def detect_and_store_language(user_id, message, user_context):
    if user_id not in user_context:
        user_context[user_id] = {}
    
    if "language" not in user_context[user_id]:  # Only detect language once
        try:
            language = detect(message)
        except:
            language = "en"  # Default to English if detection fails
        user_context[user_id]["language"] = language
    
    return user_context[user_id]["language"]