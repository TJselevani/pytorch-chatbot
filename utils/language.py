"""
Language detection and multilingual support.
"""

from typing import Dict


def detect_language(text: str) -> str:
    """Simple language detection for English and Swahili."""
    text_lower = text.lower()

    # Swahili keywords
    swahili_keywords = [
        "tafadhali",
        "nataka",
        "nini",
        "gari",
        "safari",
        "naomba",
        "hapana",
        "ndio",
        "sawa",
        "nambari",
    ]

    swahili_count = sum(1 for word in swahili_keywords if word in text_lower)

    return "sw" if swahili_count >= 2 else "en"


class MultilingualResponses:
    """Centralized multilingual response management."""

    RESPONSES = {
        "otp": {
            "request_details": {
                "en": "To send an OTP, I need your phone number and fleet number.",
                "sw": "Kutuma OTP, nahitaji nambari yako ya simu na nambari ya gari.",
            },
            "request_phone": {
                "en": "Please provide your phone number.",
                "sw": "Tafadhali toa nambari yako ya simu.",
            },
            "request_fleet": {
                "en": "Please provide your fleet number.",
                "sw": "Tafadhali toa nambari ya gari lako.",
            },
            "otp_sent": {
                "en": "OTP sent to {phone}. Please enter the code.",
                "sw": "OTP imetumwa kwa {phone}. Tafadhali ingiza nambari.",
            },
            "otp_failed": {
                "en": "Failed to send OTP. Please try again.",
                "sw": "Imeshindwa kutuma OTP. Tafadhali jaribu tena.",
            },
            "verified": {
                "en": "Verification successful!",
                "sw": "Uthibitisho umefanikiwa!",
            },
            "invalid_otp": {
                "en": "Invalid OTP. Please try again.",
                "sw": "OTP si sahihi. Tafadhali jaribu tena.",
            },
        },
        "booking": {
            "request_details": {
                "en": "Where would you like to travel? Please provide origin and destination.",
                "sw": "Unataka kusafiri wapi? Toa mahali unapoanza na unakokwenda.",
            },
            "routes_found": {
                "en": "Available routes from {origin} to {destination}:",
                "sw": "Njia zinazopatikana kutoka {origin} hadi {destination}:",
            },
            "no_routes": {
                "en": "No routes found for this journey.",
                "sw": "Hakuna njia zilizopatikana kwa safari hii.",
            },
            "booking_confirmed": {
                "en": "Booking confirmed! ID: {booking_id}",
                "sw": "Uhifadhi umethibitishwa! ID: {booking_id}",
            },
        },
        "transfer": {
            "request_details": {
                "en": "Please provide: amount, source fleet, and destination fleet.",
                "sw": "Tafadhali toa: kiasi, gari la kutoka, na gari la kwenda.",
            },
            "confirm": {
                "en": "Transfer KSh {amount} from {source} to {dest}? Reply 'yes' to confirm.",
                "sw": "Hamisha KSh {amount} kutoka {source} hadi {dest}? Jibu 'ndio' kuthibitisha.",
            },
            "completed": {
                "en": "Transfer completed successfully! Transaction ID: {txn_id}",
                "sw": "Uhamishaji umekamilika! ID ya muamala: {txn_id}",
            },
            "cancelled": {"en": "Transfer cancelled.", "sw": "Uhamishaji umesitishwa."},
        },
        "general": {
            "timeout": {
                "en": "Session expired. Please start over.",
                "sw": "Muda umeisha. Tafadhali anza upya.",
            },
            "error": {
                "en": "An error occurred. Please try again.",
                "sw": "Kuna tatizo. Tafadhali jaribu tena.",
            },
        },
    }

    @classmethod
    def get(cls, category: str, key: str, language: str = "en", **kwargs) -> str:
        """Get response in specified language with formatting."""
        try:
            template = cls.RESPONSES[category][key][language]
            return template.format(**kwargs) if kwargs else template
        except KeyError:
            # Fallback to English
            template = cls.RESPONSES[category][key]["en"]
            return template.format(**kwargs) if kwargs else template
