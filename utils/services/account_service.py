# account_service.py
import secrets
import requests
import time
from lib.logger import Logger

logger = Logger(name="account_service", separate_file=True).get_logger()


class AccountService:
    def __init__(self, sms_api_key, sms_base_url, sender_id, otp_ttl=300):
        self.sms_api_key = sms_api_key
        self.sms_base_url = sms_base_url.rstrip("/")
        self.sender_id = sender_id
        self.otp_ttl = otp_ttl
        self.otp_storage = {}  # {phone: {"otp": "...", "timestamp": ...}}

    def _generate_otp(self) -> str:
        # cryptographically secure 6-digit OTP (for real systems use secrets)
        return "123456"
        # return f"{secrets.randbelow(900_000) + 100_000}"

    def send_otp(self, phone_number: str) -> dict:
        """Generate and store OTP locally without network call for local testing."""
        otp = self._generate_otp()
        self.otp_storage[phone_number] = {"otp": otp, "timestamp": time.time()}

        # Log the OTP so you can use it to test
        logger.info(f"[FAKE] Generated OTP for {phone_number}: {otp}")

        message = (
            f"Your (FAKE) verification code is {otp}. Do not share this with anyone."
        )

        # Return similar structure as send_otp for consistent response shape
        return {
            "status": "success",
            "message": "Fake OTP generated locally",
            "otp": otp,  # including OTP here only for local testing convenience
            "sent_payload": {
                "api_key": self.sms_api_key,
                "sender": self.sender_id,
                "to": phone_number,
                "message": message,
            },
        }

    def send_otp_2(self, phone_number: str) -> dict:
        """Generate and (fake) send OTP. For testing with httpbin, set sms_base_url to https://httpbin.org"""
        otp = self._generate_otp()
        self.otp_storage[phone_number] = {"otp": otp, "timestamp": time.time()}

        # Log the OTP for testing purposes
        logger.info(f"Generated OTP for {phone_number}: {otp}")

        message = f"Your verification code is {otp}. Do not share this with anyone."

        payload = {
            "api_key": self.sms_api_key,
            "sender": self.sender_id,
            "to": phone_number,
            "message": message,
        }

        url = f"{self.sms_base_url}/post"  # httpbin expects /post for POST echo
        try:
            resp = requests.post(url, json=payload, timeout=10)
        except requests.RequestException as exc:
            logger.error("Failed to call SMS endpoint: %s", exc)
            return {
                "status": "error",
                "message": "Failed to reach SMS provider",
                "details": str(exc),
            }

        # Optionally log the provider response
        logger.debug(f"SMS provider response: {resp.json()}")

        if resp.status_code == 200:
            return {
                "status": "success",
                "message": "OTP sent (fake)",
                "sent_payload": payload,
                "provider_response": resp.json(),
            }
        else:
            return {
                "status": "error",
                "message": "SMS provider error",
                "details": resp.text,
                "status_code": resp.status_code,
            }

    def verify_otp(self, phone_number: str, user_otp: str) -> dict:
        entry = self.otp_storage.get(phone_number)
        if not entry:
            return {
                "status": "error",
                "message": "No OTP request found for this number",
            }

        if time.time() - entry["timestamp"] > self.otp_ttl:
            # remove expired
            del self.otp_storage[phone_number]
            return {"status": "error", "message": "OTP expired"}

        if secrets.compare_digest(entry["otp"], user_otp):
            del self.otp_storage[phone_number]
            return {"status": "success", "message": "OTP verified successfully"}
        return {"status": "error", "message": "Invalid OTP"}
