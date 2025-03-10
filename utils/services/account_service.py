import random
import requests
import time
from lib.logger import Logger

logger = Logger(name="account_service", separate_file=True).get_logger()


class AccountService:
    def __init__(self, sms_api_key, sms_base_url, sender_id):
        self.sms_api_key = sms_api_key
        self.sms_base_url = sms_base_url
        self.sender_id = sender_id
        self.otp_storage = {}  # Temporary store for OTPs

    def generate_otp(self):
        """Generate a random 6-digit OTP."""
        return str(random.randint(100000, 999999))

    def send_otp(self, phone_number):
        """Send an OTP to the provided phone number using an SMS API."""
        otp = self.generate_otp()
        self.otp_storage[phone_number] = {
            "otp": otp,
            "timestamp": time.time(),
        }  # Store OTP

        message = f"Your verification code is {otp}. Do not share this with anyone."
        logger.info(otp)

        payload = {
            "api_key": self.sms_api_key,
            "sender": self.sender_id,
            "to": phone_number,
            "message": message,
        }

        response = requests.post(
            f"{self.sms_base_url}/send-sms", json=payload, timeout=300
        )

        if response.status_code == 200:
            return {"status": "success", "message": "OTP sent successfully"}
        else:
            return {
                "status": "error",
                "message": "Failed to send OTP",
                "details": response.text,
            }

    def verify_otp(self, phone_number, user_otp):
        """Verify the provided OTP against the stored one."""
        if phone_number in self.otp_storage:
            stored_data = self.otp_storage[phone_number]
            stored_otp = stored_data["otp"]
            timestamp = stored_data["timestamp"]

            # Check if OTP is valid within 5 minutes (300 seconds)
            if time.time() - timestamp > 300:
                return {"status": "error", "message": "OTP expired"}

            if user_otp == stored_otp:
                del self.otp_storage[
                    phone_number
                ]  # Remove OTP after successful verification
                return {"status": "success", "message": "OTP verified successfully"}
            else:
                return {"status": "error", "message": "Invalid OTP"}

        return {"status": "error", "message": "No OTP request found for this number"}
