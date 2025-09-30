import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# main.py - Updated main application
from app.hybrid_chatbot import HybridChatBotIntegration
from utils.match import detect_language
from config import TRAINING_DATA_FILE, LANGCHAIN_CONFIG
from langchain_anthropic import ChatAnthropic

# import os
from datetime import datetime


import time
from collections import defaultdict


# Workflow timeout settings
WORKFLOW_CONFIG = {
    "otp_timeout": 300,  # 5 minutes
    "booking_timeout": 600,  # 10 minutes
    "transfer_timeout": 180,  # 3 minutes
    "route_timeout": 60,  # 1 minute
}


def create_hybrid_chatbot():
    """Factory function to create the hybrid chatbot"""

    # Set up LLM for workflows (optional - only needed for NLP-heavy workflows)
    if LANGCHAIN_CONFIG.get("api_key"):
        os.environ["ANTHROPIC_API_KEY"] = LANGCHAIN_CONFIG["api_key"]
        llm = ChatAnthropic(
            model=LANGCHAIN_CONFIG["model_name"],
            temperature=LANGCHAIN_CONFIG["temperature"],
            max_tokens=LANGCHAIN_CONFIG["max_tokens"],
        )
    else:
        llm = None  # Workflows can work without LLM for structured data extraction

    # Create hybrid chatbot
    bot = HybridChatBotIntegration(TRAINING_DATA_FILE, "Sam")

    return bot


# Usage example
if __name__ == "__main__":
    bot = create_hybrid_chatbot()

    # # # # # # # # # # #  Test OTP workflow # # # # # # # # # # # # # # # # # #
    print("=== Testing OTP Workflow ===")
    response1 = bot.process_message("user123", "Can I get an OTP Code")
    print(f"Bot: {response1['Sam']}")

    response2 = bot.process_message(
        "user123", "My phone is 0712345678 and fleet is sm34"
    )
    print(f"Bot: {response2['Sam']}")

    response3 = bot.process_message("user123", "123456")  # OTP code
    print(f"Bot: {response3['Sam']}")

    # # # # # # # # # # #  Test Booking workflow # # # # # # # # # # # # # # # # # #
    print("\n\n\n\n=== Testing Booking Workflow ===")
    response4 = bot.process_message(
        "user456", "I want to Book a ride from Nairobi to Mombasa"
    )
    print(f"Bot: {response4['Sam']}")

    response5 = bot.process_message("user456", "Book SafariCom Express")
    print(f"Bot: {response5['Sam']}")

    # # # # # # # # # # #  Test Transfer workflow # # # # # # # # # # # # # # # # # #
    print("\n\n\n\n=== Testing Transfer Workflow ===")
    response6 = bot.process_message(
        "user789", "Can you Transfer Ksh 500 from se34 to se45"
    )
    print(f"Bot: {response6['Sam']}")

    response7 = bot.process_message("user789", "yes")
    print(f"Bot: {response7['Sam']}")

    # # # # # # # # # # #  Test Route workflow # # # # # # # # # # # # # # # # # #
    print("\n\n\n\n=== Testing Route Inquiry ===")
    response8 = bot.process_message(
        "user101", "What is the fare from Nairobi to Kisumu?"
    )
    print(f"Bot: {response8['Sam']}")


# api_integration.py - Example API service integrations
class TravelAPIService:
    """Centralized API service for all travel-related operations"""

    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def search_routes(self, origin: str, destination: str, date: str = None):
        """Search for available routes"""
        endpoint = f"{self.base_url}/routes/search"
        payload = {
            "origin": origin,
            "destination": destination,
            "date": date or datetime.now().strftime("%Y-%m-%d"),
        }

        # Your actual API call implementation
        return await self._make_request("POST", endpoint, payload)

    async def create_booking(self, route_id: str, passenger_details: dict):
        """Create a new booking"""
        endpoint = f"{self.base_url}/bookings"
        payload = {
            "route_id": route_id,
            "passenger_details": passenger_details,
            "booking_time": datetime.now().isoformat(),
        }

        return await self._make_request("POST", endpoint, payload)

    async def get_fleet_balance(self, fleet_id: str):
        """Get fleet account balance"""
        endpoint = f"{self.base_url}/fleets/{fleet_id}/balance"
        return await self._make_request("GET", endpoint)

    async def transfer_funds(self, source_fleet: str, dest_fleet: str, amount: float):
        """Transfer funds between fleets"""
        endpoint = f"{self.base_url}/transfers"
        payload = {
            "source_fleet": source_fleet,
            "destination_fleet": dest_fleet,
            "amount": amount,
            "timestamp": datetime.now().isoformat(),
        }

        return await self._make_request("POST", endpoint, payload)

    async def _make_request(self, method: str, endpoint: str, payload: dict = None):
        """Make HTTP request to API"""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            if method == "GET":
                async with session.get(endpoint, headers=self.headers) as response:
                    return await response.json()
            elif method == "POST":
                async with session.post(
                    endpoint, headers=self.headers, json=payload
                ) as response:
                    return await response.json()


# workflow_monitor.py - Monitor and manage workflows
# import time
# from collections import defaultdict


class WorkflowMonitor:
    """Monitor workflow performance and user sessions"""

    def __init__(self):
        self.workflow_stats = defaultdict(list)
        self.active_sessions = {}
        self.error_counts = defaultdict(int)

    def track_workflow_start(self, user_id: str, workflow_type: str):
        """Track when a workflow starts"""
        self.workflow_stats[workflow_type].append(
            {"user_id": user_id, "start_time": time.time(), "status": "active"}
        )

    def track_workflow_end(self, user_id: str, workflow_type: str, success: bool):
        """Track when a workflow completes"""
        for stat in self.workflow_stats[workflow_type]:
            if stat["user_id"] == user_id and stat["status"] == "active":
                stat["end_time"] = time.time()
                stat["duration"] = stat["end_time"] - stat["start_time"]
                stat["status"] = "success" if success else "failed"
                break

    def get_workflow_analytics(self):
        """Get workflow performance analytics"""
        analytics = {}

        for workflow_type, stats in self.workflow_stats.items():
            completed = [s for s in stats if s["status"] in ["success", "failed"]]
            if completed:
                avg_duration = sum(s["duration"] for s in completed) / len(completed)
                success_rate = sum(
                    1 for s in completed if s["status"] == "success"
                ) / len(completed)

                analytics[workflow_type] = {
                    "total_runs": len(completed),
                    "avg_duration": avg_duration,
                    "success_rate": success_rate * 100,
                }

        return analytics

    def cleanup_stale_workflows(self, chatbot_instance, timeout_seconds: int = 1800):
        """Clean up workflows that have been inactive too long"""
        current_time = time.time()
        stale_users = []

        for user_id, workflow_data in chatbot_instance.active_workflows.items():
            # Check if workflow has been active too long
            if hasattr(workflow_data.get("state", {}), "get"):
                last_activity = workflow_data["state"].get(
                    "last_activity", current_time
                )
                if current_time - last_activity > timeout_seconds:
                    stale_users.append(user_id)

        # Clean up stale workflows
        for user_id in stale_users:
            del chatbot_instance.active_workflows[user_id]
            print(f"Cleaned up stale workflow for user {user_id}")

        return len(stale_users)


# deployment.py - Production deployment considerations
class ProductionChatBot(HybridChatBotIntegration):
    """Production-ready version with monitoring and error handling"""

    def __init__(self, file_path, bot_name="Sam"):
        super().__init__(file_path, bot_name)
        self.monitor = WorkflowMonitor()
        self.api_service = TravelAPIService(
            base_url=os.getenv("TRAVEL_API_URL"), api_key=os.getenv("TRAVEL_API_KEY")
        )

    def process_message(self, user_id, message):
        """Enhanced process_message with monitoring"""
        try:
            # Track request
            start_time = time.time()

            # Process message
            result = super().process_message(user_id, message)

            # Track success
            duration = time.time() - start_time
            self._log_request(user_id, message, result, duration, success=True)

            return result

        except Exception as e:
            # Track failure
            duration = time.time() - start_time
            self._log_request(
                user_id, message, None, duration, success=False, error=str(e)
            )

            # Return graceful fallback
            language = detect_language(message)
            fallback = {
                "en": "Sorry, I'm having trouble processing your request. Please try again.",
                "sw": "Samahani, nina shida kukusaidia. Tafadhali jaribu tena.",
            }

            return {self.bot_name: fallback.get(language, fallback["en"])}

    def _log_request(self, user_id, message, result, duration, success, error=None):
        """Log request for monitoring"""
        log_entry = {
            "user_id": user_id,
            "message_length": len(message),
            "duration": duration,
            "success": success,
            "timestamp": time.time(),
        }

        if error:
            log_entry["error"] = error

        # Your logging implementation here
        print(f"Request processed: {log_entry}")
