import requests
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RouteService:
    """Service for route information and bookings."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    def search_routes(
        self, origin: str, destination: str, date: str = None
    ) -> Dict[str, Any]:
        """Search for available routes."""
        try:
            params = {"origin": origin, "destination": destination}
            if date:
                params["date"] = date

            response = requests.get(
                f"{self.base_url}/routes/search", params=params, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to search routes: {e}")
            return {"routes": [], "success": False, "message": str(e)}

    def create_booking(
        self, route_id: str, user_id: str, passenger_count: int = 1
    ) -> Dict[str, Any]:
        """Create a booking."""
        try:
            response = requests.post(
                f"{self.base_url}/bookings/create",
                json={
                    "route_id": route_id,
                    "user_id": user_id,
                    "passenger_count": passenger_count,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create booking: {e}")
            return {"status": "error", "message": str(e)}
