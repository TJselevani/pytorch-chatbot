import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TransferService:
    """Service for handling transfers between fleets."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    def process_transfer(
        self, user_id: str, source_fleet: str, dest_fleet: str, amount: float
    ) -> Dict[str, Any]:
        """Process a transfer between fleets."""
        try:
            response = requests.post(
                f"{self.base_url}/transfers/process",
                json={
                    "user_id": user_id,
                    "source_fleet": source_fleet,
                    "dest_fleet": dest_fleet,
                    "amount": amount,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to process transfer: {e}")
            return {"status": "error", "message": str(e)}
