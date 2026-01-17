import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AccountService:
    """Service for handling OTP and account operations."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    def send_otp(self, phone: str) -> Dict[str, Any]:
        """Send OTP to phone number."""
        try:
            response = requests.post(
                f"{self.base_url}/send-otp", json={"phone": phone}, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to send OTP: {e}")
            return {"status": "error", "message": str(e)}

    def verify_otp(self, phone: str, code: str) -> Dict[str, Any]:
        """Verify OTP code."""
        try:
            response = requests.post(
                f"{self.base_url}/verify-otp",
                json={"phone": phone, "code": code},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to verify OTP: {e}")
            return {"status": "error", "message": str(e)}

    def validate_fleet(self, fleet_number: str) -> Dict[str, Any]:
        """Validate fleet number."""
        try:
            response = requests.get(
                f"{self.base_url}/validate-fleet/{fleet_number}", timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to validate fleet: {e}")
            return {"valid": False, "message": str(e)}
